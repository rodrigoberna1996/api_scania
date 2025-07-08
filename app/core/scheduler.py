from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scania_auth.jobs import refresh_scania_token
from app.services.sharepoint_auth.jobs import refresh_sharepoint_token, update_sharepoint_items

scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.get_job("refresh_token_job"):
        scheduler.add_job(
            refresh_scania_token,
            trigger="interval",
            minutes=30,
            id="refresh_token_job",
            replace_existing=True
        )

    if not scheduler.get_job("refresh_sharepoint_token_job"):
        scheduler.add_job(
            refresh_sharepoint_token,
            trigger="interval",
            minutes=30,
            id="refresh_sharepoint_token_job",
            replace_existing=True
        )

    if not scheduler.get_job("update_sharepoint_items_job"):
        scheduler.add_job(
            update_sharepoint_items,
            trigger="interval",
            #hour="0,12",
            minutes=25,
            id="update_sharepoint_items_job",
            replace_existing=True
        )

    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)
