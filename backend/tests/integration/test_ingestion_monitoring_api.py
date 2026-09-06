from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingestion_status():
    response = client.get("/api/v1/ingestion/status")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "source" in data
    assert "last_run_id" in data
    assert "last_run_status" in data
    assert "latest_data_period" in data
    assert "records_received" in data
    assert "records_inserted" in data
    assert "records_updated" in data
    assert "records_rejected" in data

    assert data["last_run_id"] is not None
    assert data["last_run_status"] is not None

    print("\nIngestion monitoring API test passed.")
    print(f"Overall status : {data['status']}")
    print(f"Source         : {data['source']}")
    print(f"Last run ID    : {data['last_run_id']}")
    print(f"Last run status: {data['last_run_status']}")
    print(f"Latest period  : {data['latest_data_period']}")


if __name__ == "__main__":
    test_ingestion_status()
    print("Ingestion monitoring API tests passed.")
