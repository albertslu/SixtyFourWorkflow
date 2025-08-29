"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

import sys
import os
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from utils.logging import setup_logging
from api import workflows, jobs
from services.job_manager import job_manager
from services.database_service import db_service

# Load environment variables from root directory
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Setup logging
setup_logging()

app = FastAPI(
    title="SixtyFour Workflow Engine",
    description="A simplified replica of Sixtyfour's Workflow Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(workflows.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "SixtyFour Workflow Engine API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from loguru import logger
    logger.info("Starting SixtyFour Workflow Engine...")
    
    # Initialize database
    await db_service.create_tables()
    
    # Start job manager
    await job_manager.start()
    
    logger.info("SixtyFour Workflow Engine started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from loguru import logger
    logger.info("Shutting down SixtyFour Workflow Engine...")
    
    # Stop job manager
    await job_manager.stop()
    
    logger.info("SixtyFour Workflow Engine shut down successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
