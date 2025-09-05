"""
Core data models for trainset management
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class TrainsetStatus(str, Enum):
    REVENUE_SERVICE = "revenue_service"
    STANDBY = "standby"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    OUT_OF_SERVICE = "out_of_service"

class CertificateType(str, Enum):
    ROLLING_STOCK = "rolling_stock"
    SIGNALLING = "signalling"
    TELECOM = "telecom"

class JobCardStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"

class FitnessCertificate(BaseModel):
    certificate_type: CertificateType
    issue_date: datetime
    expiry_date: datetime
    is_valid: bool = True
    issuing_department: str

class JobCard(BaseModel):
    job_id: str
    trainset_id: str
    status: JobCardStatus
    priority: int = Field(ge=1, le=5)  # 1=highest, 5=lowest
    estimated_hours: float
    description: str
    created_date: datetime

class BrandingContract(BaseModel):
    contract_id: str
    advertiser: str
    required_exposure_hours: float
    current_exposure_hours: float = 0.0
    start_date: date
    end_date: date
    penalty_rate: float  # per hour shortfall

class Trainset(BaseModel):
    trainset_id: str
    car_count: int = 4
    current_status: TrainsetStatus
    current_mileage: float
    last_maintenance_date: Optional[datetime] = None
    fitness_certificates: List[FitnessCertificate] = []
    job_cards: List[JobCard] = []
    branding_contract: Optional[BrandingContract] = None
    stabling_bay: Optional[int] = None
    last_cleaning_date: Optional[datetime] = None
    
    def is_service_ready(self) -> bool:
        """Check if trainset is ready for revenue service"""
        # All certificates must be valid
        if not all(cert.is_valid and cert.expiry_date > datetime.now() 
                  for cert in self.fitness_certificates):
            return False
        
        # No open high-priority job cards
        high_priority_open = any(
            jc.status == JobCardStatus.OPEN and jc.priority <= 2 
            for jc in self.job_cards
        )
        
        return not high_priority_open

class InductionDecision(BaseModel):
    trainset_id: str
    recommended_status: TrainsetStatus
    priority_score: float
    reasoning: List[str]
    conflicts: List[str] = []
    estimated_service_hours: float = 0.0