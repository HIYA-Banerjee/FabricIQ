from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base, SessionLocal
from app.simulator.factory_simulator import seed_database
from app.domains.notifications.websocket import manager
from loguru import logger
import sys

# Configure Loguru logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add(settings.LOG_FILE, rotation="10 MB", retention="10 days", level="INFO")

# Create tables
logger.info("Initializing database schemas...")
Base.metadata.create_all(bind=engine)

# Seed database if empty
db = SessionLocal()
try:
    from app.models.models import Order
    if db.query(Order).count() == 0:
        logger.info("Database is empty. Populating with multi-tenant mock data...")
        seed_database(db, "factory_alpha")
        seed_database(db, "factory_beta")
        logger.info("Database seeding completed.")
except Exception as e:
    logger.error(f"Error seeding database on startup: {str(e)}")
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Healthcheck
@app.get("/health")
def healthcheck():
    return {"status": "healthy", "project": settings.PROJECT_NAME}

# WebSocket route for dashboard clients
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep-alive loop
            data = await websocket.receive_text()
            # Echo back or parse input
            await websocket.send_json({"type": "ping", "status": "active"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
