"""
Manual input handler for operator overrides and WhatsApp updates
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ManualInputHandler:
    """
    Handler for manual operator inputs and overrides
    """
    
    def __init__(self):
        self.manual_overrides = {}
        self.whatsapp_updates = []
    
    async def initialize(self):
        """Initialize manual input handler"""
        logger.info("Initializing manual input handler...")
        
        # Load any existing manual overrides from database
        await self._load_existing_overrides()
        
        logger.info("Manual input handler initialized")
    
    async def _load_existing_overrides(self):
        """Load existing manual overrides from storage"""
        # Mock existing overrides
        self.manual_overrides = {
            "TS-005": {
                "status_override": "maintenance",
                "reason": "Operator reported unusual noise",
                "override_by": "supervisor_001",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def fetch_manual_overrides(self) -> List[Dict[str, Any]]:
        """
        Fetch current manual overrides
        
        Returns:
            List of manual override dictionaries
        """
        logger.info("Fetching manual overrides...")
        
        try:
            overrides = []
            for trainset_id, override_data in self.manual_overrides.items():
                overrides.append({
                    "trainset_id": trainset_id,
                    **override_data
                })
            
            logger.info(f"Fetched {len(overrides)} manual overrides")
            return overrides
            
        except Exception as e:
            logger.error(f"Error fetching manual overrides: {e}")
            return []
    
    async def add_manual_override(self, trainset_id: str, override_data: Dict[str, Any]) -> bool:
        """
        Add manual override for trainset
        
        Args:
            trainset_id: Trainset identifier
            override_data: Override information
            
        Returns:
            Success status
        """
        logger.info(f"Adding manual override for {trainset_id}")
        
        try:
            self.manual_overrides[trainset_id] = {
                **override_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # In production, persist to database
            # await self._persist_override(trainset_id, override_data)
            
            logger.info(f"Manual override added for {trainset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding manual override: {e}")
            return False
    
    async def remove_manual_override(self, trainset_id: str) -> bool:
        """
        Remove manual override for trainset
        
        Args:
            trainset_id: Trainset identifier
            
        Returns:
            Success status
        """
        logger.info(f"Removing manual override for {trainset_id}")
        
        try:
            if trainset_id in self.manual_overrides:
                del self.manual_overrides[trainset_id]
                
                # In production, remove from database
                # await self._remove_override_from_db(trainset_id)
                
                logger.info(f"Manual override removed for {trainset_id}")
                return True
            else:
                logger.warning(f"No override found for {trainset_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing manual override: {e}")
            return False
    
    async def process_whatsapp_update(self, message: str, sender: str) -> Dict[str, Any]:
        """
        Process WhatsApp update message
        
        Args:
            message: WhatsApp message content
            sender: Message sender identifier
            
        Returns:
            Processed update information
        """
        logger.info(f"Processing WhatsApp update from {sender}")
        
        try:
            # Simple message parsing - in production, use NLP
            update = {
                "message": message,
                "sender": sender,
                "timestamp": datetime.now().isoformat(),
                "processed": False
            }
            
            # Extract trainset mentions
            trainset_mentions = []
            words = message.upper().split()
            for word in words:
                if word.startswith("TS-") and len(word) == 6:
                    trainset_mentions.append(word)
            
            update["trainset_mentions"] = trainset_mentions
            
            # Extract status keywords
            status_keywords = ["MAINTENANCE", "REPAIR", "READY", "ISSUE", "PROBLEM"]
            found_keywords = [kw for kw in status_keywords if kw in message.upper()]
            update["status_keywords"] = found_keywords
            
            self.whatsapp_updates.append(update)
            
            logger.info(f"WhatsApp update processed: {len(trainset_mentions)} trainsets mentioned")
            return update
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp update: {e}")
            return {}
    
    async def get_recent_whatsapp_updates(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent WhatsApp updates
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent updates
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_updates = []
        for update in self.whatsapp_updates:
            update_time = datetime.fromisoformat(update["timestamp"])
            if update_time >= cutoff_time:
                recent_updates.append(update)
        
        return recent_updates