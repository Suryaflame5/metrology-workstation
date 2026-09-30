import random

def generate_telemetry_stream(samples: int = 10, nominal: float = 10.0, stdev: float = 0.00002):
    readings = [round(random.gauss(nominal, stdev), 7) for _ in range(samples)]
    return {
        "count": samples,
        "nominal": nominal,
        "mean": round(sum(readings) / samples, 7),
        "readings": readings
    }

if __name__ == "__main__":
    data = generate_telemetry_stream(5)
    print("Simulated 5 live readings:", data)
