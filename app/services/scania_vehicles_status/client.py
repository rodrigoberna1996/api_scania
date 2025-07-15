from urllib.parse import urljoin, urlparse
import httpx
from app.services.scania_auth.auth import auth_service

BASE_URL = "https://dataaccess.scania.com/rfms4"

class VehicleStatusClient:
    def __init__(self):
        self.base_url = BASE_URL

    async def get_vehicle_status(
        self,
        vin: str,
        starttime: str,
        stoptime: str,
        content_filter: str = "HEADER,SNAPSHOT,ACCUMULATED",
        latest_only: bool = False,
    ):
        token = await auth_service.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json; rfms=vehiclestatuses.v4.0"
        }

        params = {
            "vin": vin,
            "starttime": starttime,
            "stoptime": stoptime,
            "contentFilter": content_filter,
            "latestOnly": str(latest_only).lower()
        }

        async with httpx.AsyncClient() as client:
            all_statuses = []
            next_url = f"{self.base_url}/vehiclestatuses"

            while next_url:
                is_first_call = "vehiclestatuses" in urlparse(next_url).path
                response = await client.get(next_url, headers=headers, params=params if is_first_call else None)
                response.raise_for_status()
                data = response.json()

                vehicle_statuses = data.get("vehicleStatusResponse", {}).get("vehicleStatuses", [])
                all_statuses.extend(vehicle_statuses)

                if data.get("moreDataAvailable") and data.get("moreDataAvailableLink"):
                    link = data["moreDataAvailableLink"]
                    # Asegura que el link no duplique /rfms4
                    parsed_link = urlparse(link)
                    if parsed_link.scheme and parsed_link.netloc:
                        # link ya es una URL completa
                        next_url = link
                    else:
                        # link es relativo, unir sin duplicar path
                        next_url = urljoin("https://dataaccess.scania.com", link)
                    params = None  # No incluir params otra vez
                else:
                    next_url = None

        return {
            "vehicleStatusResponse": {
                "vehicleStatuses": all_statuses
            }
        }

vehicle_status_client = VehicleStatusClient()
