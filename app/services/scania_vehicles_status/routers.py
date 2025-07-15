from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.services.scania_vehicles.vehicle_map import get_vehicle_map
from app.services.scania_vehicles_status.service import (
    get_vehicle_historical_data, VehicleHistoricalData, VehicleSummaryData
)

router = APIRouter()

class VehicleHistoryResponse(BaseModel):
    historical_data: List[VehicleHistoricalData]
    summary: Optional[VehicleSummaryData]

@router.get("/", response_model=VehicleHistoryResponse)
async def vehicle_history(
    economic_number: str = Query(..., description="Número económico del tracto"),
    starttime: str = Query(..., description="Fecha/hora inicio en ISO 8601 UTC"),
    stoptime: str = Query(..., description="Fecha/hora fin en ISO 8601 UTC")
):
    economic_to_vin = await get_vehicle_map()
    vin = economic_to_vin.get(economic_number)

    if not vin:
        raise HTTPException(status_code=404, detail=f"No se encontró el VIN para el número económico {economic_number}")

    data = await get_vehicle_historical_data(vin, starttime, stoptime)
    return data
