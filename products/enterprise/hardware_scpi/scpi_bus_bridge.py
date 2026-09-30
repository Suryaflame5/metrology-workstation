import sys
import time

def query_scpi_instrument(resource_str: str, command: str) -> str:
    print(f"[SCPI BUS] Connecting to {resource_str} via VISA...")
    print(f"[SCPI TX]  {command}")
    time.sleep(0.05)
    mock_responses = {
        "*IDN?": "KEYSIGHT TECHNOLOGIES,34461A,MY53201402,A.02.17-02.40-02.17-00.52-01-01",
        "MEAS:VOLT:DC?": "+9.9999824E+00",
        "MEAS:RES?": "+1.0000041E+04"
    }
    resp = mock_responses.get(command, "+1.0000000E+00")
    print(f"[SCPI RX]  {resp}")
    return resp

if __name__ == "__main__":
    query_scpi_instrument("USB0::0x2A8D::0x1301::MY53201402::INSTR", "MEAS:VOLT:DC?")
