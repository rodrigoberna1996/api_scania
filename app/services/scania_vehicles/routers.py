from fastapi import APIRouter
from app.services.scania_vehicles.client import vehicles_client
from app.services.scania_vehicles.schemas import VehicleMapResponse

router = APIRouter()

@router.get("/", tags=["Scania"], response_model=VehicleMapResponse)
async def get_vehicle_map():
    vehicle_map = await vehicles_client.get_vehicle_map()

    return VehicleMapResponse(economic_to_vin=vehicle_map)
