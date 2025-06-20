from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scania.jobs import refresh_scania_token
from app.services.sharepoint.jobs import refresh_sharepoint_token

scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.get_job("refresh_token_job"):
        scheduler.add_job(
            refresh_scania_token,
            trigger="interval",
            minutes=5,
            id="refresh_token_job",
            replace_existing=True
        )

    if not scheduler.get_job("refresh_sharepoint_token_job"):
        scheduler.add_job(
            refresh_sharepoint_token,
            trigger="interval",
            minutes=5,
            id="refresh_sharepoint_token_job",
            replace_existing=True
        )

    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)
