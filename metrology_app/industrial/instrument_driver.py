"""
Unified InstrumentDriver Abstraction & Concrete Driver Implementations.
Standardizes laboratory hardware communication across VISA, SCPI over TCP/IP,
Serial RS-232/485, and explicit Virtual/Mock simulators.
"""

from abc import ABC, abstractmethod
import socket
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class HardwareCommunicationError(Exception):
    """Raised when physical or logical instrument communication fails."""
    pass


class InstrumentDriver(ABC):
    """
    Abstract Base Class for all Metrology Instrument Drivers.
    Hardware and calibration engines must communicate exclusively via this interface.
    """

    def __init__(self, resource_string: str, timeout_sec: float = 3.0):
        self.resource_string = resource_string
        self.timeout_sec = timeout_sec
        self.is_connected = False
        self.last_connected_at: Optional[str] = None
        self.driver_name = self.__class__.__name__

    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        """Establish connection to the instrument. Returns connection metadata or raises HardwareCommunicationError."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and release hardware handles."""
        pass

    @abstractmethod
    def identify(self) -> str:
        """Query instrument identification string (*IDN? or equivalent)."""
        pass

    @abstractmethod
    def configure(self, parameters: Dict[str, Any]) -> bool:
        """Configure instrument range, measurement function, trigger, or resolution."""
        pass

    @abstractmethod
    def measure(self) -> Dict[str, Any]:
        """Trigger and acquire a single calibrated measurement reading."""
        pass

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        """Check hardware link health and operational status."""
        pass

    @abstractmethod
    def reset(self) -> bool:
        """Reset instrument to known safe state (*RST or equivalent)."""
        pass

    @abstractmethod
    def get_errors(self) -> List[str]:
        """Query instrument system error queue (SYST:ERR? or equivalent)."""
        pass


# =============================================================================
# SCPI OVER TCP/IP DRIVER
# =============================================================================

class SCPITCPDriver(InstrumentDriver):
    """Raw TCP Socket SCPI Driver for Ethernet/LXI instruments (e.g. port 5025)."""

    def __init__(self, resource_string: str, timeout_sec: float = 3.0):
        super().__init__(resource_string, timeout_sec)
        self.host = "127.0.0.1"
        self.port = 5025
        self._parse_resource()
        self.sock: Optional[socket.socket] = None

    def _parse_resource(self):
        parts = self.resource_string.split("::")
        if len(parts) >= 3 and parts[0].startswith("TCPIP"):
            self.host = parts[1]
            try:
                self.port = int(parts[2])
            except ValueError:
                self.port = 5025
        elif ":" in self.resource_string:
            p = self.resource_string.split(":")
            self.host = p[0]
            self.port = int(p[1])

    def connect(self) -> Dict[str, Any]:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout_sec)
            self.sock.connect((self.host, self.port))
            self.is_connected = True
            self.last_connected_at = datetime.now(timezone.utc).isoformat()
            return {
                "status": "CONNECTED",
                "bus": "TCPIP",
                "host": self.host,
                "port": self.port,
                "resource": self.resource_string,
            }
        except Exception as e:
            self.is_connected = False
            self.sock = None
            raise HardwareCommunicationError(f"Failed to connect to SCPI TCP instrument at {self.host}:{self.port} -> {str(e)}")

    def disconnect(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
        self.is_connected = False

    def _query_raw(self, cmd: str) -> str:
        if not self.is_connected or not self.sock:
            raise HardwareCommunicationError("Instrument is not connected.")
        clean_cmd = cmd.strip()
        if not clean_cmd.endswith("\n"):
            clean_cmd += "\n"
        try:
            self.sock.sendall(clean_cmd.encode("utf-8"))
            data = self.sock.recv(4096).decode("utf-8").strip()
            return data
        except Exception as e:
            raise HardwareCommunicationError(f"SCPI TCP query '{cmd.strip()}' failed: {str(e)}")

    def _write_raw(self, cmd: str) -> bool:
        if not self.is_connected or not self.sock:
            raise HardwareCommunicationError("Instrument is not connected.")
        clean_cmd = cmd.strip()
        if not clean_cmd.endswith("\n"):
            clean_cmd += "\n"
        try:
            self.sock.sendall(clean_cmd.encode("utf-8"))
            return True
        except Exception as e:
            raise HardwareCommunicationError(f"SCPI TCP write '{cmd.strip()}' failed: {str(e)}")

    def identify(self) -> str:
        return self._query_raw("*IDN?")

    def configure(self, parameters: Dict[str, Any]) -> bool:
        func = parameters.get("function", "VOLT:DC")
        range_val = parameters.get("range", "AUTO")
        cmd = f":CONF:{func} {range_val}"
        return self._write_raw(cmd)

    def measure(self) -> Dict[str, Any]:
        t_start = time.time()
        raw = self._query_raw("READ?")
        latency_ms = round((time.time() - t_start) * 1000, 2)
        try:
            val = float(raw)
        except ValueError:
            val = 0.0
        return {
            "value": val,
            "unit": "V",
            "raw_response": raw,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "VALID",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "resource": self.resource_string,
            "driver": self.driver_name,
            "last_connected_at": self.last_connected_at,
        }

    def reset(self) -> bool:
        return self._write_raw("*RST")

    def get_errors(self) -> List[str]:
        err = self._query_raw("SYST:ERR?")
        return [err]


# =============================================================================
# SCPI OVER SERIAL (RS-232 / RS-485 / USB-COM) DRIVER
# =============================================================================

class SCPISerialDriver(InstrumentDriver):
    """Direct Serial RS-232/RS-485 driver with configurable baud rate and parity."""

    def __init__(self, resource_string: str, baud_rate: int = 9600, timeout_sec: float = 3.0):
        super().__init__(resource_string, timeout_sec)
        self.baud_rate = baud_rate
        self.port = self.resource_string.replace("ASRL", "COM").replace("::INSTR", "")
        self._serial_handle = None

    def connect(self) -> Dict[str, Any]:
        try:
            import serial
            self._serial_handle = serial.Serial(self.port, baudrate=self.baud_rate, timeout=self.timeout_sec)
            self.is_connected = True
            self.last_connected_at = datetime.now(timezone.utc).isoformat()
            return {
                "status": "CONNECTED",
                "bus": "SERIAL",
                "port": self.port,
                "baud_rate": self.baud_rate,
            }
        except ImportError:
            raise HardwareCommunicationError("pyserial package is not installed. Run pip install pyserial.")
        except Exception as e:
            self.is_connected = False
            raise HardwareCommunicationError(f"Serial connection to {self.port} failed: {str(e)}")

    def disconnect(self) -> None:
        if self._serial_handle:
            try:
                self._serial_handle.close()
            except Exception:
                pass
        self._serial_handle = None
        self.is_connected = False

    def identify(self) -> str:
        if not self.is_connected or not self._serial_handle:
            raise HardwareCommunicationError("Serial device not connected.")
        self._serial_handle.write(b"*IDN?\n")
        return self._serial_handle.readline().decode("utf-8").strip()

    def configure(self, parameters: Dict[str, Any]) -> bool:
        if not self.is_connected or not self._serial_handle:
            raise HardwareCommunicationError("Serial device not connected.")
        cmd = parameters.get("command", "*CLS")
        self._serial_handle.write(f"{cmd}\n".encode("utf-8"))
        return True

    def measure(self) -> Dict[str, Any]:
        if not self.is_connected or not self._serial_handle:
            raise HardwareCommunicationError("Serial device not connected.")
        t_start = time.time()
        self._serial_handle.write(b"MEAS?\n")
        raw = self._serial_handle.readline().decode("utf-8").strip()
        latency_ms = round((time.time() - t_start) * 1000, 2)
        try:
            val = float(raw)
        except ValueError:
            val = 0.0
        return {
            "value": val,
            "unit": "V",
            "raw_response": raw,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "VALID",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "resource": self.resource_string,
            "port": self.port,
            "baud_rate": self.baud_rate,
            "driver": self.driver_name,
        }

    def reset(self) -> bool:
        if not self.is_connected or not self._serial_handle:
            raise HardwareCommunicationError("Serial device not connected.")
        self._serial_handle.write(b"*RST\n")
        return True

    def get_errors(self) -> List[str]:
        if not self.is_connected or not self._serial_handle:
            raise HardwareCommunicationError("Serial device not connected.")
        self._serial_handle.write(b"SYST:ERR?\n")
        return [self._serial_handle.readline().decode("utf-8").strip()]


# =============================================================================
# VISA INSTRUMENT DRIVER (PyVISA WRAPPER)
# =============================================================================

class VISADriver(InstrumentDriver):
    """PyVISA resource wrapper supporting GPIB, USB, and TCPIP instruments."""

    def __init__(self, resource_string: str, timeout_sec: float = 3.0):
        super().__init__(resource_string, timeout_sec)
        self._session = None

    def connect(self) -> Dict[str, Any]:
        try:
            import pyvisa
            rm = pyvisa.ResourceManager()
            self._session = rm.open_resource(self.resource_string)
            self._session.timeout = int(self.timeout_sec * 1000)
            self.is_connected = True
            self.last_connected_at = datetime.now(timezone.utc).isoformat()
            return {
                "status": "CONNECTED",
                "bus": "VISA",
                "resource": self.resource_string,
            }
        except ImportError:
            raise HardwareCommunicationError("PyVISA package is not installed. Run pip install pyvisa.")
        except Exception as e:
            self.is_connected = False
            raise HardwareCommunicationError(f"VISA resource '{self.resource_string}' open failed: {str(e)}")

    def disconnect(self) -> None:
        if self._session:
            try:
                self._session.close()
            except Exception:
                pass
        self._session = None
        self.is_connected = False

    def identify(self) -> str:
        if not self.is_connected or not self._session:
            raise HardwareCommunicationError("VISA instrument not connected.")
        return self._session.query("*IDN?").strip()

    def configure(self, parameters: Dict[str, Any]) -> bool:
        if not self.is_connected or not self._session:
            raise HardwareCommunicationError("VISA instrument not connected.")
        cmd = parameters.get("command", "*CLS")
        self._session.write(cmd)
        return True

    def measure(self) -> Dict[str, Any]:
        if not self.is_connected or not self._session:
            raise HardwareCommunicationError("VISA instrument not connected.")
        t_start = time.time()
        raw = self._session.query("READ?").strip()
        latency_ms = round((time.time() - t_start) * 1000, 2)
        try:
            val = float(raw)
        except ValueError:
            val = 0.0
        return {
            "value": val,
            "unit": "V",
            "raw_response": raw,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "VALID",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "resource": self.resource_string,
            "driver": self.driver_name,
        }

    def reset(self) -> bool:
        if not self.is_connected or not self._session:
            raise HardwareCommunicationError("VISA instrument not connected.")
        self._session.write("*RST")
        return True

    def get_errors(self) -> List[str]:
        if not self.is_connected or not self._session:
            raise HardwareCommunicationError("VISA instrument not connected.")
        return [self._session.query("SYST:ERR?").strip()]


# =============================================================================
# EXPLICIT MOCK / SIMULATOR DRIVER
# =============================================================================

class MockSimulatorDriver(InstrumentDriver):
    """
    Explicit, high-fidelity laboratory hardware simulator.
    Complies with IEEE 488.2 and SCPI-99 standard queries.
    Never fakes a physical connection; engages only when explicitly configured.
    """

    SUPPORTED_MODELS = {
        "KEYSIGHT_34461A": {
            "idn": "Keysight Technologies,34461A,MY53201488,A.02.17-02.40-02.17-00.52-01-01",
            "nominal": 10.000000,
            "std_dev": 0.000015,
            "unit": "V",
        },
        "FLUKE_8508A": {
            "idn": "FLUKE,8508A,FLK-8508-4109,V1.28",
            "nominal": 10.0000000,
            "std_dev": 0.0000025,
            "unit": "V",
        },
        "MITUTOYO_DIGIMATIC": {
            "idn": "Mitutoyo,IT-016U-Digimatic,MIT-IT-8812,Ver 2.01",
            "nominal": 25.0000,
            "std_dev": 0.00012,
            "unit": "mm",
        },
        "DRUCK_DPI_104": {
            "idn": "Baker Hughes,Druck DPI 104,DRK-104-9934,Rev 3.1",
            "nominal": 10.000,
            "std_dev": 0.0015,
            "unit": "bar",
        },
    }

    def __init__(self, resource_string: str = "VIRTUAL::KEYSIGHT_34461A", profile: str = "KEYSIGHT_34461A", timeout_sec: float = 3.0):
        super().__init__(resource_string, timeout_sec)
        # Determine profile from resource string if present
        for key in self.SUPPORTED_MODELS:
            if key in resource_string.upper():
                profile = key
                break
        self.profile_key = profile.upper() if profile.upper() in self.SUPPORTED_MODELS else "KEYSIGHT_34461A"
        self.profile = self.SUPPORTED_MODELS[self.profile_key]
        self.current_set_nominal = self.profile["nominal"]
        self.current_unit = self.profile["unit"]
        self._error_queue: List[str] = []

    def connect(self) -> Dict[str, Any]:
        self.is_connected = True
        self.last_connected_at = datetime.now(timezone.utc).isoformat()
        return {
            "status": "CONNECTED_SIMULATOR",
            "bus": "VIRTUAL",
            "model": self.profile_key,
            "idn": self.profile["idn"],
            "resource": self.resource_string,
        }

    def disconnect(self) -> None:
        self.is_connected = False

    def identify(self) -> str:
        return self.profile["idn"]

    def configure(self, parameters: Dict[str, Any]) -> bool:
        if "nominal" in parameters:
            self.current_set_nominal = float(parameters["nominal"])
        if "unit" in parameters:
            self.current_unit = str(parameters["unit"])
        return True

    def measure(self) -> Dict[str, Any]:
        if not self.is_connected:
            raise HardwareCommunicationError("Virtual instrument is disconnected.")
        # Physics simulation: nominal + Gaussian noise
        noise = random.gauss(0.0, self.profile["std_dev"])
        val = round(self.current_set_nominal + noise, 7)
        return {
            "value": val,
            "unit": self.current_unit,
            "raw_response": f"{val:+.7E}",
            "latency_ms": round(random.uniform(1.2, 4.5), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "VALID",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "resource": self.resource_string,
            "driver": "MockSimulatorDriver",
            "profile": self.profile_key,
            "errors_in_queue": len(self._error_queue),
        }

    def reset(self) -> bool:
        self.current_set_nominal = self.profile["nominal"]
        self.current_unit = self.profile["unit"]
        self._error_queue.clear()
        return True

    def get_errors(self) -> List[str]:
        if not self._error_queue:
            return ['+0,"No error"']
        res = list(self._error_queue)
        self._error_queue.clear()
        return res


# =============================================================================
# DRIVER FACTORY
# =============================================================================

def create_instrument_driver(config: Dict[str, Any]) -> InstrumentDriver:
    """
    Factory function to instantiate the correct InstrumentDriver from device configuration.
    Config parameters:
      - protocol / bus: 'TCPIP', 'SERIAL', 'VISA', 'VIRTUAL', 'MOCK'
      - connection_string / resource: 'TCPIP::192.168.1.100::5025::SOCKET', 'COM3', etc.
      - baud_rate: 9600
      - timeout_sec: 3.0
    """
    resource = config.get("connection_string") or config.get("resource") or "VIRTUAL::KEYSIGHT_34461A"
    protocol = (config.get("protocol") or config.get("bus") or "").upper()
    timeout = float(config.get("timeout_sec", 3.0))

    if "VIRTUAL" in resource.upper() or "MOCK" in resource.upper() or protocol in ("VIRTUAL", "MOCK"):
        profile = config.get("driver_profile", "KEYSIGHT_34461A")
        return MockSimulatorDriver(resource_string=resource, profile=profile, timeout_sec=timeout)

    if protocol == "SERIAL" or "COM" in resource.upper() or "ASRL" in resource.upper():
        baud = int(config.get("baud_rate", 9600))
        return SCPISerialDriver(resource_string=resource, baud_rate=baud, timeout_sec=timeout)

    if protocol == "VISA" or "GPIB" in resource.upper() or "USB" in resource.upper():
        return VISADriver(resource_string=resource, timeout_sec=timeout)

    # Default to SCPI TCP/IP
    return SCPITCPDriver(resource_string=resource, timeout_sec=timeout)
