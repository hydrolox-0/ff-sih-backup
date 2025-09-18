"""
Core optimization engine for trainset induction scheduling
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import numpy as np
from ortools.linear_solver import pywraplp
from models.trainset import Trainset, TrainsetStatus, InductionDecision
import logging
from config.loader import config_loader

logger = logging.getLogger(__name__)

class InductionScheduler:
    """
    Multi-objective optimization engine for trainset allocation
    """
    
    def __init__(self):
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        self.weights = {
            'service_readiness': 0.3,
            'mileage_balance': 0.2,
            'branding_priority': 0.2,
            'maintenance_urgency': 0.15,
            'stabling_efficiency': 0.15
        }
    
    def optimize_induction(self, trainsets: List[Trainset], 
                          service_demand: int = 20) -> List[InductionDecision]:
        """
        Generate optimal trainset allocation decisions
        
        Args:
            trainsets: List of available trainsets
            service_demand: Number of trainsets needed for revenue service
            
        Returns:
            List of induction decisions with reasoning
        """
        logger.info(f"Optimizing induction for {len(trainsets)} trainsets, demand: {service_demand}")
        
        decisions = []
        
        # Calculate scores for each trainset
        scored_trainsets = []
        for trainset in trainsets:
            score = self._calculate_composite_score(trainset)
            scored_trainsets.append((trainset, score))
        
        # Sort by score (highest first)
        scored_trainsets.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate based on constraints and priorities
        service_count = 0
        standby_count = 0
        
        for trainset, score in scored_trainsets:
            decision = self._make_allocation_decision(
                trainset, score, service_count, standby_count, service_demand
            )
            
            if decision.recommended_status == TrainsetStatus.REVENUE_SERVICE:
                service_count += 1
            elif decision.recommended_status == TrainsetStatus.STANDBY:
                standby_count += 1
                
            decisions.append(decision)
        
        logger.info(f"Allocation complete: {service_count} service, {standby_count} standby")
        return decisions
    
    def _calculate_composite_score(self, trainset: Trainset) -> float:
        """Calculate weighted composite score for trainset priority"""
        
        # Service readiness score
        readiness_score = 1.0 if trainset.is_service_ready() else 0.0
        
        # Mileage balance score (prefer lower mileage)
        avg_mileage = 50000  # Assumed fleet average
        mileage_score = max(0, 1 - (trainset.current_mileage - avg_mileage) / avg_mileage)
        
        # Branding priority score
        branding_score = 0.5  # Default
        if trainset.branding_contract:
            exposure_ratio = (trainset.branding_contract.current_exposure_hours / 
                            trainset.branding_contract.required_exposure_hours)
            branding_score = max(0, 1 - exposure_ratio)
        
        # Maintenance urgency (prefer recently maintained)
        maintenance_score = 0.5
        if trainset.last_maintenance_date:
            days_since = (datetime.now() - trainset.last_maintenance_date).days
            maintenance_score = min(1.0, days_since / 30)  # Normalize to 30 days
        
        # Stabling efficiency (prefer lower bay numbers for easier access)
        stabling_score = 0.5
        if trainset.stabling_bay:
            total_trainsets = config_loader.get_total_trainsets()
            stabling_score = max(0, 1 - trainset.stabling_bay / total_trainsets)
        
        # Calculate weighted composite score
        composite_score = (
            self.weights['service_readiness'] * readiness_score +
            self.weights['mileage_balance'] * mileage_score +
            self.weights['branding_priority'] * branding_score +
            self.weights['maintenance_urgency'] * maintenance_score +
            self.weights['stabling_efficiency'] * stabling_score
        )
        
        return composite_score
    
    def _make_allocation_decision(self, trainset: Trainset, score: float,
                                current_service: int, current_standby: int,
                                service_demand: int) -> InductionDecision:
        """Make allocation decision for individual trainset"""
        
        reasoning = []
        conflicts = []
        
        # Check if trainset must go to maintenance
        if not trainset.is_service_ready():
            reasoning.append("Trainset not service-ready due to certificates or job cards")
            return InductionDecision(
                trainset_id=trainset.trainset_id,
                recommended_status=TrainsetStatus.MAINTENANCE,
                priority_score=score,
                reasoning=reasoning,
                conflicts=conflicts
            )
        
        # Allocate to revenue service if demand not met
        if current_service < service_demand:
            reasoning.append(f"Allocated to service (demand: {service_demand}, current: {current_service})")
            reasoning.append(f"Composite score: {score:.3f}")
            
            return InductionDecision(
                trainset_id=trainset.trainset_id,
                recommended_status=TrainsetStatus.REVENUE_SERVICE,
                priority_score=score,
                reasoning=reasoning,
                conflicts=conflicts,
                estimated_service_hours=16.0  # Typical service day
            )
        
        # Otherwise allocate to standby
        reasoning.append("Allocated to standby - service demand met")
        return InductionDecision(
            trainset_id=trainset.trainset_id,
            recommended_status=TrainsetStatus.STANDBY,
            priority_score=score,
            reasoning=reasoning,
            conflicts=conflicts
        )
    
    def simulate_scenario(self, trainsets: List[Trainset], 
                         scenario_changes: Dict) -> List[InductionDecision]:
        """
        Run what-if simulation with modified parameters
        
        Args:
            trainsets: Base trainset data
            scenario_changes: Dictionary of changes to apply
            
        Returns:
            Simulated allocation decisions
        """
        # Apply scenario changes to trainsets
        modified_trainsets = self._apply_scenario_changes(trainsets, scenario_changes)
        
        # Run optimization on modified data
        return self.optimize_induction(modified_trainsets)
    
    def _apply_scenario_changes(self, trainsets: List[Trainset], 
                              changes: Dict) -> List[Trainset]:
        """Apply scenario modifications to trainset data"""
        # Implementation would modify trainset properties based on scenario
        # For now, return original trainsets
        return trainsets.copy()