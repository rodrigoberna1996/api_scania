from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.scania_auth.routers import router as scania_router
from app.services.reporting_service.routers import router as reporting_router
from app.services.scania_vehicles.routers import router as vehicles_router
from app.services.scania_vehicles_status.routers import router as vehicle_history_router

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

app.include_router(scania_router, prefix="/api/scania_auth", tags=["Scania"])
app.include_router(reporting_router, prefix="/api/reporting", tags=["Reporting"])
app.include_router(vehicles_router, prefix="/api/scania_vehicles", tags=["Scania Vehicles"])
app.include_router(vehicle_history_router, prefix="/api/vehicle_history", tags=["Vehicle History"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
