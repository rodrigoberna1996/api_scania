import httpx
from app.services.scania_auth.auth import auth_service
from app.config import settings

class VehicleEvaluationClient:
    def __init__(self, base_url: str = settings.BASE_URL):
        self.base_url = base_url

    async def get_evaluation(self, vin: str, start_date: str, end_date: str) -> dict:
        token = await auth_service.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        params = {
            "vinOfInterest": vin,
            "startDate": start_date,
            "endDate": end_date,
        }
        url = f"{self.base_url}/cs/vehicle/reports/VehicleEvaluationReport/v2"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

evaluation_client = VehicleEvaluationClient()

