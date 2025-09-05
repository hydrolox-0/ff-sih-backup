#!/usr/bin/env python3
"""
Kochi Metro Trainset Induction Decision Support System
Main application entry point
"""

import uvicorn
from fastapi import FastAPI
from api.routes import router
from optimization.scheduler import InductionScheduler
from data_ingestion.manager import DataManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KMRL Trainset Induction System",
    description="Decision support system for daily trainset allocation",
    version="1.0.0"
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    logger.info("Starting KMRL Induction System...")
    
    # Initialize data manager
    data_manager = DataManager()
    await data_manager.initialize()
    
    # Initialize scheduler
    scheduler = InductionScheduler()
    
    logger.info("System initialized successfully")

@app.get("/")
async def root():
    return {"message": "KMRL Trainset Induction System", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "system": "kmrl-induction"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )