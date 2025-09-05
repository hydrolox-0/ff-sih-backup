"""
FastAPI routes for the induction system
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
from models.trainset import Trainset, InductionDecision
from optimization.scheduler import InductionScheduler
from data_ingestion.manager import DataManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency injection
async def get_data_manager():
    return DataManager()

async def get_scheduler():
    return InductionScheduler()

@router.get("/trainsets", response_model=List[Trainset])
async def get_all_trainsets(data_manager: DataManager = Depends(get_data_manager)):
    """Get all trainset data"""
    try:
        trainsets = await data_manager.get_all_trainsets()
        return trainsets
    except Exception as e:
        logger.error(f"Error fetching trainsets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trainset data")

@router.get("/trainsets/{trainset_id}", response_model=Trainset)
async def get_trainset(trainset_id: str, data_manager: DataManager = Depends(get_data_manager)):
    """Get specific trainset data"""
    try:
        trainset = await data_manager.get_trainset(trainset_id)
        if not trainset:
            raise HTTPException(status_code=404, detail="Trainset not found")
        return trainset
    except Exception as e:
        logger.error(f"Error fetching trainset {trainset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trainset data")

@router.post("/optimize", response_model=List[InductionDecision])
async def optimize_induction(
    service_demand: int = 20,
    data_manager: DataManager = Depends(get_data_manager),
    scheduler: InductionScheduler = Depends(get_scheduler)
):
    """Generate optimized induction decisions"""
    try:
        # Get current trainset data
        trainsets = await data_manager.get_all_trainsets()
        
        # Run optimization
        decisions = scheduler.optimize_induction(trainsets, service_demand)
        
        logger.info(f"Generated {len(decisions)} induction decisions")
        return decisions
        
    except Exception as e:
        logger.error(f"Error optimizing induction: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize induction")

@router.post("/simulate", response_model=List[InductionDecision])
async def simulate_scenario(
    scenario_changes: Dict[str, Any],
    service_demand: int = 20,
    data_manager: DataManager = Depends(get_data_manager),
    scheduler: InductionScheduler = Depends(get_scheduler)
):
    """Run what-if simulation with scenario changes"""
    try:
        # Get current trainset data
        trainsets = await data_manager.get_all_trainsets()
        
        # Run simulation
        decisions = scheduler.simulate_scenario(trainsets, scenario_changes)
        
        logger.info(f"Simulation complete: {len(decisions)} decisions generated")
        return decisions
        
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to run simulation")

@router.post("/manual-override")
async def add_manual_override(
    trainset_id: str,
    override_data: Dict[str, Any],
    data_manager: DataManager = Depends(get_data_manager)
):
    """Add manual override for trainset"""
    try:
        success = await data_manager.manual_input.add_manual_override(trainset_id, override_data)
        
        if success:
            return {"message": f"Manual override added for {trainset_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add manual override")
            
    except Exception as e:
        logger.error(f"Error adding manual override: {e}")
        raise HTTPException(status_code=500, detail="Failed to add manual override")

@router.delete("/manual-override/{trainset_id}")
async def remove_manual_override(
    trainset_id: str,
    data_manager: DataManager = Depends(get_data_manager)
):
    """Remove manual override for trainset"""
    try:
        success = await data_manager.manual_input.remove_manual_override(trainset_id)
        
        if success:
            return {"message": f"Manual override removed for {trainset_id}"}
        else:
            raise HTTPException(status_code=404, detail="No override found for trainset")
            
    except Exception as e:
        logger.error(f"Error removing manual override: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove manual override")

@router.post("/refresh-data")
async def refresh_data(data_manager: DataManager = Depends(get_data_manager)):
    """Refresh data from all sources"""
    try:
        trainsets = await data_manager.refresh_all_data()
        
        return {
            "message": "Data refreshed successfully",
            "trainsets_updated": len(trainsets),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh data")

@router.get("/system/status")
async def get_system_status():
    """Get system health and status"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "data_manager": "healthy",
            "scheduler": "healthy",
            "api": "healthy"
        }
    }