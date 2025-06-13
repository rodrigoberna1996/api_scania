import httpx
from app.config import settings

BASE_URL = settings.BASE_URL

class ScaniaClient:
    def __init__(self):
        self.client_id = settings.CLIENT_ID
        self.secret_key = settings.SECRET_KEY
        self.base_url = BASE_URL

    async def get_challenge(self) -> str:
        url = f"{self.base_url}/auth/clientid2challenge"
        data = {"clientId": self.client_id}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, data=data)
            r.raise_for_status()
            return r.json()["challenge"]

    async def get_token(self, challenge_response: str) -> dict:
        url = f"{self.base_url}/auth/response2token"
        data = {"clientId": self.client_id, "Response": challenge_response}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, data=data)
            r.raise_for_status()
            return r.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        url = f"{self.base_url}/auth/refreshtoken"
        data = {"clientId": self.client_id, "RefreshToken": refresh_token}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, data=data)
            r.raise_for_status()
            return r.json()
