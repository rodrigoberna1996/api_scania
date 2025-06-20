from app.services.scania.auth import auth_service

async def refresh_scania_token():
    await auth_service.refresh_token()
