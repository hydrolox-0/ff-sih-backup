"""
Configuration loader for the KMRL Trainset Induction System
"""

import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    """Load and manage system configuration"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if self._config is None:
            try:
                with open(self.config_path, 'r') as file:
                    self._config = yaml.safe_load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing configuration file: {e}")
        
        return self._config
    
    def get_fleet_config(self) -> Dict[str, Any]:
        """Get fleet configuration"""
        config = self.load_config()
        return config.get('fleet', {})
    
    def get_total_trainsets(self) -> int:
        """Get total number of trainsets"""
        fleet_config = self.get_fleet_config()
        return fleet_config.get('total_trainsets', 25)
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get optimization configuration"""
        config = self.load_config()
        return config.get('optimization', {})
    
    def get_data_sources_config(self) -> Dict[str, Any]:
        """Get data sources configuration"""
        config = self.load_config()
        return config.get('data_sources', {})
    
    def get_maintenance_config(self) -> Dict[str, Any]:
        """Get maintenance configuration"""
        config = self.load_config()
        return config.get('maintenance', {})

# Global config instance
config_loader = ConfigLoader()