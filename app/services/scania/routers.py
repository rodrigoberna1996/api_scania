# app/services/scania/routers.py
from fastapi import APIRouter
from app.services.scania.auth_service import auth_service

router = APIRouter()

@router.post("/token/refresh", tags=["Dev"])
async def manual_refresh_token():
    token = await auth_service.refresh_token()
    return {"token": token}

@router.get("/token", tags=["Dev"])
async def get_token():
    token = await auth_service.get_token()
    return {"token": token}