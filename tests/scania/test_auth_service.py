import pytest
import asyncio
from app.services.scania.auth import auth_service

@pytest.mark.asyncio
async def test_token_fetch():
    token = await auth_service.get_token()
    assert token is not None
