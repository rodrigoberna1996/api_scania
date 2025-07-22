import pytest
from datetime import datetime, timedelta

from app.services.scania_vehicles_status import service

@pytest.mark.asyncio
async def test_segmented_vehicle_status(monkeypatch):
    calls = []

    async def fake_get_vehicle_status(*, vin, starttime, stoptime, content_filter="", latest_only=False):
        calls.append((starttime, stoptime))
        idx = len(calls)
        return {
            "vehicleStatusResponse": {
                "vehicleStatuses": [
                    {
                        "createdDateTime": starttime,
                        "hrTotalVehicleDistance": idx * 1000,
                        "engineTotalFuelUsed": idx * 100,
                        "snapshotData": {"catalystFuelLevel": 50 - idx}
                    }
                ]
            }
        }

    async def fake_get_evaluation(vin, start_date, end_date):
        return {}

    monkeypatch.setattr(service.vehicle_status_client, "get_vehicle_status", fake_get_vehicle_status)
    monkeypatch.setattr(service.evaluation_client, "get_evaluation", fake_get_evaluation)

    start = datetime(2024, 1, 1)
    end = start + timedelta(days=12)
    result = await service.get_vehicle_historical_data(
        "VIN1",
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    assert len(calls) == 3
    assert len(result["historical_data"]) == 3
