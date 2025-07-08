from app.services.scania_auth.auth import auth_service

async def refresh_scania_token():
    await auth_service.refresh_token()
