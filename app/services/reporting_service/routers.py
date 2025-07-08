from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.reporting_service.service import generate_excel_report
from app.services.sharepoint_auth.jobs import update_sharepoint_items


router = APIRouter()

@router.get("/report")
async def report_endpoint(session: AsyncSession = Depends(get_db)):
    return await generate_excel_report(session)

@router.get("/pull/data")
async def pull_data_report():
    return await update_sharepoint_items()
