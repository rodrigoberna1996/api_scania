from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scania.jobs import refresh_token_job

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.get_job("refresh_token_job"):
        scheduler.add_job(
            refresh_token_job,
            trigger="interval",
            minutes=55,
            id="refresh_token_job",
            replace_existing=True
        )
    if not scheduler.running:
        scheduler.start()

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)
