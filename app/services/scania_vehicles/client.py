from app.core.redis_client import get_redis_client
from app.config import settings
import httpx
import json
from app.services.scania_auth.auth import auth_service

REDIS_KEY = "scania_vehicle_map"
CACHE_TTL = 3600  # 1 hora

class ScaniaVehiclesClient:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.client = httpx.AsyncClient()

    async def fetch_vehicles_from_api(self):
        url = f"{self.base_url}/rfms4/vehicles"
        token = await auth_service.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json; rfms=vehicles.v4.0",
        }

        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Validación extra para evitar errores futuros
        if "vehicleResponse" not in data or "vehicles" not in data["vehicleResponse"]:
            raise ValueError("La respuesta de la API de Scania no contiene el campo esperado 'vehicleResponse.vehicles'")

        return data["vehicleResponse"]["vehicles"]

    async def get_vehicle_map(self) -> dict[str, str]:
        redis_client = get_redis_client()
        cached = await redis_client.get(REDIS_KEY)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass  # Si hay corrupción, seguimos a la API

        vehicles = await self.fetch_vehicles_from_api()

        vehicle_map = {
            v["customerVehicleName"]: v["vin"]
            for v in vehicles
            if "customerVehicleName" in v and "vin" in v
        }

        await redis_client.set(REDIS_KEY, json.dumps(vehicle_map), ex=CACHE_TTL)
        return vehicle_map

vehicles_client = ScaniaVehiclesClient()
