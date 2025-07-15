from typing import Dict
from app.services.scania_vehicles.client import vehicles_client

async def get_vehicle_map() -> Dict[str, str]:
    """
    Retorna un dict con mapeo de No. Económico -> VIN desde Redis o desde la API si no existe caché.
    """
    vehicle_map = await vehicles_client.get_vehicle_map()

    if not isinstance(vehicle_map, dict):
        raise ValueError("El mapa de vehículos no tiene el formato esperado (dict[str, str])")

    return vehicle_map
