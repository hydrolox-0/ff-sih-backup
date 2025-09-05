"""
Data ingestion manager for multiple sources
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from models.trainset import Trainset, FitnessCertificate, JobCard, CertificateType, JobCardStatus
from .maximo_connector import MaximoConnector
from .iot_connector import IoTConnector
from .manual_input import ManualInputHandler

logger = logging.getLogger(__name__)

class DataManager:
    """
    Centralized data ingestion and synchronization manager
    """
    
    def __init__(self):
        self.maximo_connector = MaximoConnector()
        self.iot_connector = IoTConnector()
        self.manual_input = ManualInputHandler()
        self.trainsets_cache = {}
        self.last_update = None
    
    async def initialize(self):
        """Initialize all data connectors"""
        logger.info("Initializing data connectors...")
        
        await self.maximo_connector.initialize()
        await self.iot_connector.initialize()
        await self.manual_input.initialize()
        
        logger.info("Data connectors initialized")
    
    async def refresh_all_data(self) -> List[Trainset]:
        """
        Refresh data from all sources and return updated trainset list
        """
        logger.info("Refreshing data from all sources...")
        
        try:
            # Fetch data from all sources concurrently
            maximo_data, iot_data, manual_data = await asyncio.gather(
                self.maximo_connector.fetch_job_cards(),
                self.iot_connector.fetch_fitness_data(),
                self.manual_input.fetch_manual_overrides(),
                return_exceptions=True
            )
            
            # Merge data into trainset objects
            trainsets = await self._merge_data_sources(maximo_data, iot_data, manual_data)
            
            # Update cache
            self.trainsets_cache = {ts.trainset_id: ts for ts in trainsets}
            self.last_update = datetime.now()
            
            logger.info(f"Data refresh complete: {len(trainsets)} trainsets updated")
            return trainsets
            
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            raise
    
    async def _merge_data_sources(self, maximo_data: List[Dict], 
                                iot_data: List[Dict], 
                                manual_data: List[Dict]) -> List[Trainset]:
        """
        Merge data from multiple sources into Trainset objects
        """
        trainsets = {}
        
        # Initialize trainsets with basic info
        for i in range(1, 26):  # 25 trainsets
            trainset_id = f"TS-{i:03d}"
            trainsets[trainset_id] = Trainset(
                trainset_id=trainset_id,
                current_status="standby",
                current_mileage=45000 + (i * 1000),  # Mock data
                fitness_certificates=[],
                job_cards=[]
            )
        
        # Add Maximo job card data
        if isinstance(maximo_data, list):
            for job_data in maximo_data:
                trainset_id = job_data.get('trainset_id')
                if trainset_id in trainsets:
                    job_card = JobCard(
                        job_id=job_data['job_id'],
                        trainset_id=trainset_id,
                        status=JobCardStatus(job_data['status']),
                        priority=job_data['priority'],
                        estimated_hours=job_data['estimated_hours'],
                        description=job_data['description'],
                        created_date=datetime.fromisoformat(job_data['created_date'])
                    )
                    trainsets[trainset_id].job_cards.append(job_card)
        
        # Add IoT fitness certificate data
        if isinstance(iot_data, list):
            for cert_data in iot_data:
                trainset_id = cert_data.get('trainset_id')
                if trainset_id in trainsets:
                    certificate = FitnessCertificate(
                        certificate_type=CertificateType(cert_data['type']),
                        issue_date=datetime.fromisoformat(cert_data['issue_date']),
                        expiry_date=datetime.fromisoformat(cert_data['expiry_date']),
                        is_valid=cert_data['is_valid'],
                        issuing_department=cert_data['department']
                    )
                    trainsets[trainset_id].fitness_certificates.append(certificate)
        
        # Apply manual overrides
        if isinstance(manual_data, list):
            for override in manual_data:
                trainset_id = override.get('trainset_id')
                if trainset_id in trainsets:
                    # Apply manual status overrides
                    if 'status_override' in override:
                        trainsets[trainset_id].current_status = override['status_override']
        
        return list(trainsets.values())
    
    async def get_trainset(self, trainset_id: str) -> Trainset:
        """Get specific trainset data"""
        if trainset_id in self.trainsets_cache:
            return self.trainsets_cache[trainset_id]
        
        # If not in cache, refresh data
        await self.refresh_all_data()
        return self.trainsets_cache.get(trainset_id)
    
    async def get_all_trainsets(self) -> List[Trainset]:
        """Get all trainset data"""
        if not self.trainsets_cache or not self.last_update:
            await self.refresh_all_data()
        
        return list(self.trainsets_cache.values())