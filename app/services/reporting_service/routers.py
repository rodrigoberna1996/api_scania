from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.reporting_service.service import generate_excel_report
from app.services.sharepoint_auth.jobs import update_sharepoint_items
from datetime import datetime

router = APIRouter()

@router.get("/report")
async def report_endpoint(
    session: AsyncSession = Depends(get_db),
    mes: int = Query(default=None, description="Mes numérico para filtrar, 1-12")
):
    mes_actual = datetime.now().month
    mes = mes if mes is not None else mes_actual
    return await generate_excel_report(session, mes)

@router.get("/pull/data")
async def pull_data_report():
    return await update_sharepoint_items()
