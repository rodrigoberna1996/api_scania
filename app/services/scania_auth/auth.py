# app/services/scania_auth/auth.py

from typing import Optional
import httpx
from app.core.redis_client import get_redis_client
from app.core.security import create_challenge_response
from app.config import settings
from app.services.scania_auth.client import ScaniaClient

REDIS_TOKEN_KEY = "scania_api_token"
REDIS_REFRESH_TOKEN_KEY = "scania_refresh_token"

class ScaniaAuthService:
    def __init__(self):
        self.client = ScaniaClient()
        self.redis = get_redis_client()

    async def _get_token_from_redis(self) -> Optional[str]:
        return await self.redis.get(REDIS_TOKEN_KEY)

    async def _get_refresh_token_from_redis(self) -> Optional[str]:
        return await self.redis.get(REDIS_REFRESH_TOKEN_KEY)

    async def _save_tokens_to_redis(self, token: str, refresh_token: str):
        await self.redis.set(REDIS_TOKEN_KEY, token, ex=settings.TOKEN_EXPIRE_SECONDS)
        await self.redis.set(REDIS_REFRESH_TOKEN_KEY, refresh_token, ex=86400)

    async def fetch_new_token(self):
        challenge = await self.client.get_challenge()
        response = create_challenge_response(settings.SECRET_KEY, challenge)
        token_data = await self.client.get_token(response)
        await self._save_tokens_to_redis(token_data["token"], token_data["refreshToken"])
        return token_data["token"]

    async def refresh_token(self):
        refresh_token = await self._get_refresh_token_from_redis()
        if not refresh_token:
            return await self.fetch_new_token()
        try:
            token_data = await self.client.refresh_token(refresh_token)
        except httpx.HTTPStatusError:
            return await self.fetch_new_token()
        await self._save_tokens_to_redis(token_data["token"], token_data["refreshToken"])
        return token_data["token"]

    async def get_token(self) -> str:
        token = await self._get_token_from_redis()
        if token:
            return token
        return await self.fetch_new_token()


auth_service = ScaniaAuthService()
