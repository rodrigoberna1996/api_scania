import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SharePointAuthService:
    TOKEN_URL = "https://login.microsoftonline.com/206805c7-24a4-4581-9843-e227b0ee55b1/oauth2/v2.0/token"

    def __init__(self):
        self.client_id = settings.SHAREPOINT_CLIENT_ID
        self.client_secret = settings.SHAREPOINT_CLIENT_SECRET
        self.scope = "https://graph.microsoft.com/.default"

    async def get_access_token(self) -> Optional[str]:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.TOKEN_URL, data=data, headers=headers)
                response.raise_for_status()
                return response.json().get("access_token")
            except httpx.HTTPStatusError as e:
                logger.error(f"Error al obtener token SharePoint: {e.response.text}")

        return None
