"""
Tests for optimization engine
"""

import pytest
from datetime import datetime, timedelta
from models.trainset import Trainset, TrainsetStatus, FitnessCertificate, JobCard, CertificateType, JobCardStatus
from optimization.scheduler import InductionScheduler

def create_test_trainset(trainset_id: str, service_ready: bool = True) -> Trainset:
    """Create a test trainset with basic data"""
    
    certificates = [
        FitnessCertificate(
            certificate_type=CertificateType.ROLLING_STOCK,
            issue_date=datetime.now() - timedelta(days=30),
            expiry_date=datetime.now() + timedelta(days=335),
            is_valid=service_ready,
            issuing_department="Rolling Stock"
        ),
        FitnessCertificate(
            certificate_type=CertificateType.SIGNALLING,
            issue_date=datetime.now() - timedelta(days=15),
            expiry_date=datetime.now() + timedelta(days=350),
            is_valid=service_ready,
            issuing_department="Signalling"
        ),
        FitnessCertificate(
            certificate_type=CertificateType.TELECOM,
            issue_date=datetime.now() - timedelta(days=45),
            expiry_date=datetime.now() + timedelta(days=180),
            is_valid=service_ready,
            issuing_department="Telecom"
        )
    ]
    
    job_cards = []
    if not service_ready:
        job_cards.append(JobCard(
            job_id=f"TEST-{trainset_id}",
            trainset_id=trainset_id,
            status=JobCardStatus.OPEN,
            priority=1,
            estimated_hours=4.0,
            description="Test maintenance job",
            created_date=datetime.now()
        ))
    
    return Trainset(
        trainset_id=trainset_id,
        current_status=TrainsetStatus.STANDBY,
        current_mileage=50000,
        fitness_certificates=certificates,
        job_cards=job_cards
    )

def test_scheduler_initialization():
    """Test scheduler initialization"""
    scheduler = InductionScheduler()
    assert scheduler is not None
    assert scheduler.solver is not None
    assert len(scheduler.weights) == 5

def test_service_readiness_check():
    """Test trainset service readiness logic"""
    # Service ready trainset
    ready_trainset = create_test_trainset("TS-001", service_ready=True)
    assert ready_trainset.is_service_ready() == True
    
    # Not service ready trainset
    not_ready_trainset = create_test_trainset("TS-002", service_ready=False)
    assert not_ready_trainset.is_service_ready() == False

def test_optimization_basic():
    """Test basic optimization functionality"""
    scheduler = InductionScheduler()
    
    # Create test trainsets
    trainsets = [
        create_test_trainset("TS-001", service_ready=True),
        create_test_trainset("TS-002", service_ready=True),
        create_test_trainset("TS-003", service_ready=False),
        create_test_trainset("TS-004", service_ready=True),
        create_test_trainset("TS-005", service_ready=True)
    ]
    
    # Run optimization
    decisions = scheduler.optimize_induction(trainsets, service_demand=3)
    
    # Verify results
    assert len(decisions) == 5
    
    # Count allocations
    service_count = sum(1 for d in decisions if d.recommended_status == TrainsetStatus.REVENUE_SERVICE)
    maintenance_count = sum(1 for d in decisions if d.recommended_status == TrainsetStatus.MAINTENANCE)
    
    # Should have 3 in service, 1 in maintenance (not service ready)
    assert service_count == 3
    assert maintenance_count >= 1

def test_composite_score_calculation():
    """Test composite score calculation"""
    scheduler = InductionScheduler()
    
    trainset = create_test_trainset("TS-001", service_ready=True)
    score = scheduler._calculate_composite_score(trainset)
    
    # Score should be between 0 and 1
    assert 0 <= score <= 1
    
    # Service ready trainset should have higher score than not ready
    not_ready_trainset = create_test_trainset("TS-002", service_ready=False)
    not_ready_score = scheduler._calculate_composite_score(not_ready_trainset)
    
    assert score > not_ready_score

def test_allocation_constraints():
    """Test allocation respects constraints"""
    scheduler = InductionScheduler()
    
    # Create more trainsets than service demand
    trainsets = [create_test_trainset(f"TS-{i:03d}", service_ready=True) for i in range(1, 11)]
    
    decisions = scheduler.optimize_induction(trainsets, service_demand=5)
    
    # Should allocate exactly 5 to service
    service_count = sum(1 for d in decisions if d.recommended_status == TrainsetStatus.REVENUE_SERVICE)
    assert service_count == 5

if __name__ == "__main__":
    pytest.main([__file__])