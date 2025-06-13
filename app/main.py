from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.scania.routers import router as scania_router
from app.core.scheduler import start_scheduler, shutdown_scheduler
import uvicorn
from app.utils import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()

app = FastAPI(
    title="My Microservice API",
    description="API para múltiples servicios incluyendo Scania",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Status"])
def health_check():
    return {
        "status": "online",
        "service": "My Microservice API",
        "version": "1.0.0"
    }

app.include_router(scania_router, prefix="/api/scania", tags=["Scania"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
