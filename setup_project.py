import os

project_name = "my_project"

structure = {
    "app": {
        "__init__.py": "",
        "main.py": '''from fastapi import FastAPI
from app.services.scania_auth.routers import router as scania_router
from app.core.scheduler import start_scheduler

app = FastAPI(title="My Scania Microservice")

app.include_router(scania_router, prefix="/scania_auth", tags=["Scania"])

@app.on_event("startup")
async def startup_event():
    start_scheduler()
''',

        "config.py": '''from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLIENT_ID: str
    SECRET_KEY: str
    REDIS_URL: str = "redis://localhost:6379"
    TOKEN_EXPIRE_SECONDS: int = 3600  # 1 hour

    class Config:
        env_file = ".env"

settings = Settings()
''',

        "core": {
            "__init__.py": "",
            "redis_client.py": '''import redis.asyncio as redis
from app.config import settings

redis_client: redis.Redis | None = None

def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return redis_client
''',

            "scheduler.py": '''from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
''',

            "security.py": '''import hashlib
import hmac
import base64

def base64url_encode(arg: bytes) -> str:
    s = base64.b64encode(arg).decode("utf-8")
    s = s.rstrip("=")
    s = s.replace("+", "-")
    s = s.replace("/", "_")
    return s

def base64url_decode(arg: str) -> bytes:
    s = arg
    s = s.replace("-", "+")
    s = s.replace("_", "/")
    strlen = len(s) % 4
    if strlen == 2:
        s += "=="
    elif strlen == 3:
        s += "="
    elif strlen != 0:
        raise ValueError("Illegal base64Url string")
    return base64.b64decode(s)

def create_challenge_response(secret_key: str, challenge: str) -> str:
    secret_key_bytes = base64url_decode(secret_key)
    challenge_bytes = base64url_decode(challenge)
    hmac_digest = hmac.new(secret_key_bytes, challenge_bytes, hashlib.sha256).digest()
    return base64url_encode(hmac_digest)
'''
        },

        "services": {
            "__init__.py": "",
            "scania_auth": {
                "__init__.py": "",
                "client.py": '''import httpx
from app.config import settings

BASE_URL = "https://dataaccess.scania.com"

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
''',

                "auth.py": '''from typing import Optional
import asyncio

from app.core.redis_client import get_redis_client
from app.core.security import create_challenge_response
from app.config import settings
from app.services.scania_auth.client import ScaniaClient
from app.core.scheduler import scheduler

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
        await self.redis.set(REDIS_REFRESH_TOKEN_KEY, refresh_token, ex=86400)  # 24 hours

    async def fetch_new_token(self):
        challenge = await self.client.get_challenge()
        response = create_challenge_response(settings.SECRET_KEY, challenge)
        token_data = await self.client.get_token(response)
        await self._save_tokens_to_redis(token_data["token"], token_data["refreshToken"])
        return token_data["token"]

    async def refresh_token(self):
        refresh_token = await self._get_refresh_token_from_redis()
        if not refresh_token:
            # If no refresh token, get a new token by full challenge
            return await self.fetch_new_token()
        token_data = await self.client.refresh_token(refresh_token)
        await self._save_tokens_to_redis(token_data["token"], token_data["refreshToken"])
        return token_data["token"]

    async def get_token(self) -> str:
        token = await self._get_token_from_redis()
        if token:
            return token
        # If no token cached, fetch a new one
        return await self.fetch_new_token()


auth_service = ScaniaAuthService()

async def refresh_token_job():
    await auth_service.refresh_token()

# Scheduler setup to refresh token every 55 minutes
scheduler.add_job(refresh_token_job, 'interval', minutes=55)
''',

                "routers.py": '''from fastapi import APIRouter
from app.services.scania_auth.auth_service import auth_service

router = APIRouter()

# Ya no dejamos endpoint para token (según lo pedido)
''',

                "schemas.py": '''from pydantic import BaseModel

class TokenResponse(BaseModel):
    token: str
    refreshToken: str
'''
                ,

                "utils.py": '''# Aquí puedes agregar utilidades específicas para Scania
'''
            }
        },

        "db": {
            "__init__.py": "",
            "session.py": '''# Aquí podrías configurar SQLAlchemy o cualquier ORM para servicios CRUD futuros
'''
        }
    },

    "tests": {
        "scania_auth": {
            "__init__.py": "",
            "test_auth_service.py": '''import pytest
import asyncio
from app.services.scania_auth.auth_service import auth_service

@pytest.mark.asyncio
async def test_token_fetch():
    token = await auth_service.get_token()
    assert token is not None
'''
        }
    },

    ".env": '''CLIENT_ID=tu_client_id_aqui
SECRET_KEY=tu_secret_key_aqui
REDIS_URL=redis://localhost:6379
''',

    "requirements.txt": '''fastapi
uvicorn[standard]
httpx[http2]
redis>=4.2.0
pydantic-settings
apscheduler
pytest
pytest-asyncio
'''
}

def create_files(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_files(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    create_files(".", structure)
    print("Estructura de proyecto y archivos base creados.")
