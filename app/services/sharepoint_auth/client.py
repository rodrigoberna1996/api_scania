# app/services/sharepoint_auth/client.py

import httpx
from app.config import settings
from app.core.redis_client import get_redis_client

SHAREPOINT_TOKEN_KEY = "sharepoint_access_token"

class SharePointClient:
    def __init__(self):
        self.token_url = "https://login.microsoftonline.com/206805c7-24a4-4581-9843-e227b0ee55b1/oauth2/v2.0/token"
        self.client_id = settings.SHAREPOINT_CLIENT_ID
        self.client_secret = settings.SHAREPOINT_CLIENT_SECRET
        self.scope = "https://graph.microsoft.com/.default"
        self.redis = get_redis_client()

    async def get_token_from_api(self) -> dict:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(self.token_url, data=data, headers=headers)
            r.raise_for_status()
            return r.json()

    async def store_token(self, token: str, expires_in: int = 3590):
        await self.redis.set(SHAREPOINT_TOKEN_KEY, token, ex=expires_in)

    async def get_access_token(self) -> str:
        token = await self.redis.get(SHAREPOINT_TOKEN_KEY)
        if token:
            return token

        # No hay token, se genera uno nuevo
        token_data = await self.get_token_from_api()
        token = token_data.get("access_token")
        expires_in = int(token_data.get("expires_in", 3590))
        await self.store_token(token, expires_in)
        return token
