"""
IoT sensor connector for fitness certificate data
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IoTConnector:
    """
    Connector for IoT fitness monitoring sensors
    """
    
    def __init__(self):
        self.mqtt_broker = "mqtt.kmrl.kerala.gov.in"  # Mock broker
        self.redis_client = None
        self.connected = False
    
    async def initialize(self):
        """Initialize IoT connections"""
        logger.info("Initializing IoT connector...")
        
        # In production, initialize MQTT and Redis connections
        # self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        self.connected = True
        logger.info("IoT connector initialized")
    
    async def fetch_fitness_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fitness certificate data from IoT sensors
        
        Returns:
            List of fitness certificate dictionaries
        """
        logger.info("Fetching fitness data from IoT sensors...")
        
        try:
            # Mock fitness certificate data
            base_date = datetime.now()
            mock_certificates = []
            
            # Generate certificates for all trainsets
            for i in range(1, 26):
                trainset_id = f"TS-{i:03d}"
                
                # Rolling stock certificate
                mock_certificates.append({
                    "trainset_id": trainset_id,
                    "type": "rolling_stock",
                    "issue_date": (base_date - timedelta(days=30)).isoformat(),
                    "expiry_date": (base_date + timedelta(days=335)).isoformat(),
                    "is_valid": True,
                    "department": "Rolling Stock"
                })
                
                # Signalling certificate
                mock_certificates.append({
                    "trainset_id": trainset_id,
                    "type": "signalling", 
                    "issue_date": (base_date - timedelta(days=15)).isoformat(),
                    "expiry_date": (base_date + timedelta(days=350)).isoformat(),
                    "is_valid": True,
                    "department": "Signalling"
                })
                
                # Telecom certificate (some expired for testing)
                is_valid = i not in [3, 7, 12]  # Make some invalid for testing
                expiry_days = 180 if is_valid else -5
                
                mock_certificates.append({
                    "trainset_id": trainset_id,
                    "type": "telecom",
                    "issue_date": (base_date - timedelta(days=45)).isoformat(),
                    "expiry_date": (base_date + timedelta(days=expiry_days)).isoformat(),
                    "is_valid": is_valid,
                    "department": "Telecom"
                })
            
            logger.info(f"Fetched {len(mock_certificates)} fitness certificates")
            return mock_certificates
            
        except Exception as e:
            logger.error(f"Error fetching IoT data: {e}")
            return []
    
    async def get_real_time_status(self, trainset_id: str) -> Dict[str, Any]:
        """
        Get real-time status for specific trainset
        
        Args:
            trainset_id: Trainset identifier
            
        Returns:
            Real-time status data
        """
        logger.info(f"Getting real-time status for {trainset_id}")
        
        try:
            # Mock real-time data
            mock_status = {
                "trainset_id": trainset_id,
                "location": "Depot Bay 5",
                "battery_level": 98.5,
                "door_status": "all_closed",
                "hvac_status": "operational",
                "brake_pressure": "normal",
                "last_update": datetime.now().isoformat()
            }
            
            return mock_status
            
        except Exception as e:
            logger.error(f"Error getting real-time status: {e}")
            return {}
    
    async def subscribe_to_alerts(self, callback):
        """
        Subscribe to real-time alerts from IoT sensors
        
        Args:
            callback: Function to call when alert received
        """
        logger.info("Subscribing to IoT alerts...")
        
        # In production, implement MQTT subscription
        # def on_message(client, userdata, message):
        #     alert_data = json.loads(message.payload.decode())
        #     asyncio.create_task(callback(alert_data))
        
        logger.info("IoT alert subscription active")
    
    async def close(self):
        """Close IoT connections"""
        if self.redis_client:
            self.redis_client.close()
        self.connected = False