"""
What-if scenario simulation engine
"""

import copy
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.trainset import Trainset, TrainsetStatus, JobCard, FitnessCertificate
from optimization.scheduler import InductionScheduler
import logging

logger = logging.getLogger(__name__)

class ScenarioEngine:
    """
    Engine for running what-if scenarios on trainset allocation
    """
    
    def __init__(self):
        self.scheduler = InductionScheduler()
        self.base_scenarios = {
            "certificate_expiry": self._simulate_certificate_expiry,
            "emergency_maintenance": self._simulate_emergency_maintenance,
            "increased_demand": self._simulate_increased_demand,
            "equipment_failure": self._simulate_equipment_failure,
            "weather_impact": self._simulate_weather_impact
        }
    
    def run_scenario(self, trainsets: List[Trainset], 
                    scenario_type: str, 
                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a specific scenario simulation
        
        Args:
            trainsets: Base trainset data
            scenario_type: Type of scenario to simulate
            parameters: Scenario-specific parameters
            
        Returns:
            Simulation results with comparison
        """
        logger.info(f"Running scenario: {scenario_type}")
        
        # Get baseline allocation
        baseline_decisions = self.scheduler.optimize_induction(trainsets.copy())
        
        # Apply scenario modifications
        if scenario_type in self.base_scenarios:
            modified_trainsets = self.base_scenarios[scenario_type](trainsets, parameters)
        else:
            modified_trainsets = self._apply_custom_scenario(trainsets, parameters)
        
        # Get scenario allocation
        scenario_decisions = self.scheduler.optimize_induction(modified_trainsets)
        
        # Compare results
        comparison = self._compare_allocations(baseline_decisions, scenario_decisions)
        
        return {
            "scenario_type": scenario_type,
            "parameters": parameters,
            "baseline_decisions": baseline_decisions,
            "scenario_decisions": scenario_decisions,
            "comparison": comparison,
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_certificate_expiry(self, trainsets: List[Trainset], 
                                   parameters: Dict[str, Any]) -> List[Trainset]:
        """Simulate certificate expiry scenario"""
        modified_trainsets = copy.deepcopy(trainsets)
        
        # Parameters: trainset_ids, certificate_type
        affected_trainsets = parameters.get('trainset_ids', [])
        cert_type = parameters.get('certificate_type', 'telecom')
        
        for trainset in modified_trainsets:
            if trainset.trainset_id in affected_trainsets:
                # Mark certificates as expired
                for cert in trainset.fitness_certificates:
                    if cert.certificate_type == cert_type:
                        cert.is_valid = False
                        cert.expiry_date = datetime.now() - timedelta(days=1)
        
        logger.info(f"Simulated {cert_type} certificate expiry for {len(affected_trainsets)} trainsets")
        return modified_trainsets
    
    def _simulate_emergency_maintenance(self, trainsets: List[Trainset], 
                                      parameters: Dict[str, Any]) -> List[Trainset]:
        """Simulate emergency maintenance scenario"""
        modified_trainsets = copy.deepcopy(trainsets)
        
        # Parameters: trainset_ids, maintenance_hours
        affected_trainsets = parameters.get('trainset_ids', [])
        maintenance_hours = parameters.get('maintenance_hours', 8)
        
        for trainset in modified_trainsets:
            if trainset.trainset_id in affected_trainsets:
                # Add emergency job card
                emergency_job = JobCard(
                    job_id=f"EMRG-{trainset.trainset_id}-{datetime.now().strftime('%Y%m%d')}",
                    trainset_id=trainset.trainset_id,
                    status="open",
                    priority=1,  # Highest priority
                    estimated_hours=maintenance_hours,
                    description="Emergency maintenance - safety critical",
                    created_date=datetime.now()
                )
                trainset.job_cards.append(emergency_job)
        
        logger.info(f"Simulated emergency maintenance for {len(affected_trainsets)} trainsets")
        return modified_trainsets
    
    def _simulate_increased_demand(self, trainsets: List[Trainset], 
                                 parameters: Dict[str, Any]) -> List[Trainset]:
        """Simulate increased service demand scenario"""
        # This scenario doesn't modify trainsets, but affects optimization parameters
        # The scheduler would need to be called with different service_demand parameter
        logger.info("Simulated increased demand scenario")
        return copy.deepcopy(trainsets)
    
    def _simulate_equipment_failure(self, trainsets: List[Trainset], 
                                  parameters: Dict[str, Any]) -> List[Trainset]:
        """Simulate equipment failure scenario"""
        modified_trainsets = copy.deepcopy(trainsets)
        
        # Parameters: trainset_id, failure_type, repair_hours
        trainset_id = parameters.get('trainset_id')
        failure_type = parameters.get('failure_type', 'HVAC')
        repair_hours = parameters.get('repair_hours', 12)
        
        for trainset in modified_trainsets:
            if trainset.trainset_id == trainset_id:
                # Force trainset out of service
                trainset.current_status = TrainsetStatus.MAINTENANCE
                
                # Add failure job card
                failure_job = JobCard(
                    job_id=f"FAIL-{trainset_id}-{datetime.now().strftime('%Y%m%d')}",
                    trainset_id=trainset_id,
                    status="open",
                    priority=1,
                    estimated_hours=repair_hours,
                    description=f"{failure_type} system failure",
                    created_date=datetime.now()
                )
                trainset.job_cards.append(failure_job)
        
        logger.info(f"Simulated {failure_type} failure for {trainset_id}")
        return modified_trainsets
    
    def _simulate_weather_impact(self, trainsets: List[Trainset], 
                               parameters: Dict[str, Any]) -> List[Trainset]:
        """Simulate weather impact scenario (e.g., flooding, storms)"""
        modified_trainsets = copy.deepcopy(trainsets)
        
        # Parameters: affected_bays, impact_duration_hours
        affected_bays = parameters.get('affected_bays', [])
        impact_duration = parameters.get('impact_duration_hours', 24)
        
        for trainset in modified_trainsets:
            if trainset.stabling_bay in affected_bays:
                # Add weather-related maintenance
                weather_job = JobCard(
                    job_id=f"WTHR-{trainset.trainset_id}-{datetime.now().strftime('%Y%m%d')}",
                    trainset_id=trainset.trainset_id,
                    status="open",
                    priority=2,
                    estimated_hours=impact_duration,
                    description="Weather impact inspection and cleaning",
                    created_date=datetime.now()
                )
                trainset.job_cards.append(weather_job)
        
        logger.info(f"Simulated weather impact for bays {affected_bays}")
        return modified_trainsets
    
    def _apply_custom_scenario(self, trainsets: List[Trainset], 
                             parameters: Dict[str, Any]) -> List[Trainset]:
        """Apply custom scenario modifications"""
        modified_trainsets = copy.deepcopy(trainsets)
        
        # Apply custom modifications based on parameters
        for modification in parameters.get('modifications', []):
            trainset_id = modification.get('trainset_id')
            changes = modification.get('changes', {})
            
            for trainset in modified_trainsets:
                if trainset.trainset_id == trainset_id:
                    # Apply changes to trainset
                    for field, value in changes.items():
                        if hasattr(trainset, field):
                            setattr(trainset, field, value)
        
        return modified_trainsets
    
    def _compare_allocations(self, baseline: List, scenario: List) -> Dict[str, Any]:
        """Compare baseline and scenario allocations"""
        
        # Count allocations by status
        baseline_counts = {}
        scenario_counts = {}
        
        for decision in baseline:
            status = decision.recommended_status
            baseline_counts[status] = baseline_counts.get(status, 0) + 1
        
        for decision in scenario:
            status = decision.recommended_status
            scenario_counts[status] = scenario_counts.get(status, 0) + 1
        
        # Calculate differences
        differences = {}
        all_statuses = set(baseline_counts.keys()) | set(scenario_counts.keys())
        
        for status in all_statuses:
            baseline_count = baseline_counts.get(status, 0)
            scenario_count = scenario_counts.get(status, 0)
            differences[status] = scenario_count - baseline_count
        
        # Identify changed trainsets
        changed_trainsets = []
        baseline_dict = {d.trainset_id: d.recommended_status for d in baseline}
        scenario_dict = {d.trainset_id: d.recommended_status for d in scenario}
        
        for trainset_id in baseline_dict:
            if baseline_dict[trainset_id] != scenario_dict.get(trainset_id):
                changed_trainsets.append({
                    'trainset_id': trainset_id,
                    'baseline_status': baseline_dict[trainset_id],
                    'scenario_status': scenario_dict.get(trainset_id)
                })
        
        return {
            'baseline_counts': baseline_counts,
            'scenario_counts': scenario_counts,
            'differences': differences,
            'changed_trainsets': changed_trainsets,
            'total_changes': len(changed_trainsets)
        }