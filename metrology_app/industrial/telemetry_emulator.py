"""
Industrial Hardware Telemetry & Sensor Emulator.
Simulates real-time measurement streams with realistic Gaussian noise, thermal expansion drift, and jitter.
"""

import random
import time
from typing import Dict, Any, List


def generate_live_telemetry_sample(
    nominal_value: float = 25.00000,
    noise_std_dev: float = 0.00012,
    drift_rate_per_sec: float = 0.000001,
    elapsed_seconds: float = 0.0,
    ambient_temp_base: float = 20.0,
) -> Dict[str, Any]:
    """
    Generate a high-fidelity physical telemetry data point.
    """
    thermal_swing = 0.25 * (random.random() - 0.5)
    ambient_temp = ambient_temp_base + thermal_swing
    
    # Physical thermal expansion delta L = alpha * L * delta_T (alpha = 11.5 ppm/K for steel)
    cte = 11.5e-6
    delta_t = ambient_temp - 20.0
    thermal_expansion_error = nominal_value * cte * delta_t

    # Cumulative mechanical aging drift + ADC noise
    aging_drift = drift_rate_per_sec * elapsed_seconds
    adc_noise = random.gauss(0, noise_std_dev)

    simulated_reading = nominal_value + thermal_expansion_error + aging_drift + adc_noise

    return {
        "timestamp_unix": time.time(),
        "nominal_value_mm": nominal_value,
        "simulated_reading_mm": round(simulated_reading, 6),
        "thermal_error_mm": round(thermal_expansion_error, 7),
        "aging_drift_mm": round(aging_drift, 7),
        "adc_noise_mm": round(adc_noise, 7),
        "environmental_sensors": {
            "ambient_temperature_c": round(ambient_temp, 2),
            "relative_humidity_pct": round(45.0 + random.uniform(-1.5, 1.5), 1),
            "barometric_pressure_hpa": round(1013.25 + random.uniform(-0.5, 0.5), 2),
        },
        "instrument_status": {
            "pll_lock": True,
            "settling_time_ms": 12,
            "battery_level_pct": 98,
        },
    }
