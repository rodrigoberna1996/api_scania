from app.services.scania.auth_service import auth_service

async def refresh_token_job():
    await auth_service.refresh_token()
