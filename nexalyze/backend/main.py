from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from config.settings import settings
from database.connections import init_databases
from api.routes import router
from agents.crew_manager import CrewManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

crew_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Nexalyze Backend...")

    # Initialize databases
    await init_databases()

    # Initialize CrewAI manager
    global crew_manager
    crew_manager = CrewManager()

    # Load initial data in background
    logger.info("Loading initial startup data...")
    try:
        from services.data_service import DataService
        data_service = DataService()
        
        # Sync YC data in background (non-blocking) - Load 500 companies
        import asyncio
        asyncio.create_task(data_service.sync_yc_data(limit=500))
        logger.info("Initial data loading started in background (500 companies)")
    except Exception as e:
        logger.warning(f"Could not load initial data: {e}")

    logger.info("Backend startup complete!")

    yield

    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Nexalyze API",
    description="AI-powered competitive intelligence and startup research platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Nexalyze API is running!", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-10-09T23:00:00Z"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
