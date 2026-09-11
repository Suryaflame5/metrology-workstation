import io
import datetime
import openpyxl
import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.services.universal_importer import parse_excel_workbook, parse_raw_data_stream


def create_test_excel_binary() -> bytes:
    wb = openpyxl.Workbook()
    
    # Sheet 1: Main Calibration Data
    ws1 = wb.active
    ws1.title = "Voltage_Calibration"
    # Row 1-2: Banner title
    ws1.append(["ACCREDITED LABORATORY CALIBRATION LOG - ISO 17025"])
    ws1.append([])
    # Row 3: Real headers
    ws1.append(["Point", "Nominal_V", "Measured_Reading_V", "Timestamp", "Temp_C", "Status"])
    # Rows 4-8: Data with naive datetime
    base_time = datetime.datetime(2026, 9, 10, 14, 30, 0)
    ws1.append([1, 10.0, 10.000021, base_time, 20.15, "PASS"])
    ws1.append([2, 10.0, 9.999984, base_time + datetime.timedelta(seconds=1), 20.16, "PASS"])
    ws1.append([3, 10.0, 10.000015, base_time + datetime.timedelta(seconds=2), 20.14, "PASS"])
    ws1.append([4, 10.0, 9.999992, base_time + datetime.timedelta(seconds=3), 20.15, "PASS"])
    ws1.append([5, 10.0, 10.000033, base_time + datetime.timedelta(seconds=4), 20.15, "PASS"])
    
    # Sheet 2: Environment
    ws2 = wb.create_sheet(title="Environmental_Log")
    ws2.append(["Sensor", "Value", "Unit"])
    ws2.append(["Ambient_Temp", 20.15, "degC"])
    ws2.append(["Humidity", 46.2, "%RH"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_openpyxl_excel_binary_parsing_direct():
    excel_bytes = create_test_excel_binary()
    sheet_names, rows, headers = parse_excel_workbook(excel_bytes)

    assert "Voltage_Calibration" in sheet_names
    assert "Environmental_Log" in sheet_names
    assert len(rows) == 5
    assert "Nominal_V" in headers
    assert "Measured_Reading_V" in headers
    assert "10" in str(rows[0]["Nominal_V"])
    assert float(rows[0]["Measured_Reading_V"]) > 9.99


def test_openpyxl_excel_sheet_selection():
    excel_bytes = create_test_excel_binary()
    sheet_names, rows, headers = parse_excel_workbook(excel_bytes, sheet_name="Environmental_Log")

    assert len(rows) == 2
    assert "Sensor" in headers
    assert rows[0]["Sensor"] == "Ambient_Temp"
    assert rows[1]["Sensor"] == "Humidity"


def test_api_upload_file_preview_excel():
    client = TestClient(app)
    excel_bytes = create_test_excel_binary()

    response = client.post(
        "/api/v1/import/upload-file",
        files={"file": ("fluke_calibration.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"target_unit": "V"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "fluke_calibration.xlsx"
    assert data["total_rows"] == 5
    assert "Voltage_Calibration" in data["sheet_names"]
    assert "Measured_Reading_V" in data["headers"]
    assert data["mapping"]["Measured_Reading_V"]["role"] == "measured"
    assert len(data["extracted_summary"]["raw_measurements"]) == 5


def test_api_upload_file_preview_csv():
    client = TestClient(app)
    csv_content = b"Point,Nominal,Measured,Unit\n1,10.0,10.0001,V\n2,10.0,10.0002,V\n3,10.0,9.9999,V\n"

    response = client.post(
        "/api/v1/import/upload-file",
        files={"file": ("readings.csv", io.BytesIO(csv_content), "text/csv")},
        data={"target_unit": "V"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_rows"] == 3
    assert len(data["extracted_summary"]["raw_measurements"]) == 3

