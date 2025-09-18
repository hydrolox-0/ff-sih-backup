"""
Machine learning feedback engine for improving predictions
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime, timedelta
import pickle
import logging
from config.loader import config_loader

logger = logging.getLogger(__name__)

class LearningEngine:
    """
    Machine learning engine for learning from historical outcomes
    """
    
    def __init__(self):
        self.models = {
            'service_hours_predictor': RandomForestRegressor(n_estimators=100, random_state=42),
            'maintenance_duration_predictor': RandomForestRegressor(n_estimators=100, random_state=42),
            'failure_probability_predictor': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        self.is_trained = {model: False for model in self.models}
        self.feature_columns = []
        
    def collect_historical_data(self) -> pd.DataFrame:
        """
        Collect historical operational data for training
        
        Returns:
            DataFrame with historical features and outcomes
        """
        logger.info("Collecting historical data...")
        
        # Mock historical data - in production, fetch from database
        np.random.seed(42)
        n_samples = 1000
        
        total_trainsets = config_loader.get_total_trainsets()
        data = {
            'trainset_id': [f"TS-{i%total_trainsets+1:03d}" for i in range(n_samples)],
            'date': [datetime.now() - timedelta(days=i//total_trainsets) for i in range(n_samples)],
            'mileage': np.random.normal(50000, 15000, n_samples),
            'days_since_maintenance': np.random.exponential(15, n_samples),
            'certificate_days_remaining': np.random.uniform(1, 365, n_samples),
            'open_job_cards': np.random.poisson(1.5, n_samples),
            'priority_score': np.random.uniform(0, 1, n_samples),
            'allocated_status': np.random.choice(['service', 'standby', 'maintenance'], n_samples),
            'actual_service_hours': np.random.normal(14, 3, n_samples),
            'maintenance_duration_hours': np.random.exponential(6, n_samples),
            'failure_occurred': np.random.binomial(1, 0.05, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Add derived features
        df['mileage_normalized'] = (df['mileage'] - df['mileage'].mean()) / df['mileage'].std()
        df['maintenance_urgency'] = 1 / (df['days_since_maintenance'] + 1)
        df['certificate_urgency'] = 1 / (df['certificate_days_remaining'] + 1)
        
        logger.info(f"Collected {len(df)} historical records")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """
        Prepare feature matrix and target variables
        
        Args:
            df: Historical data DataFrame
            
        Returns:
            Tuple of (features, targets_dict)
        """
        # Feature columns
        self.feature_columns = [
            'mileage_normalized', 'days_since_maintenance', 'certificate_days_remaining',
            'open_job_cards', 'priority_score', 'maintenance_urgency', 'certificate_urgency'
        ]
        
        X = df[self.feature_columns].fillna(0)
        
        # Target variables
        targets = {
            'service_hours': df['actual_service_hours'].fillna(0),
            'maintenance_duration': df['maintenance_duration_hours'].fillna(0),
            'failure_probability': df['failure_occurred'].fillna(0)
        }
        
        return X, targets
    
    def train_models(self, df: pd.DataFrame = None) -> Dict[str, float]:
        """
        Train all ML models on historical data
        
        Args:
            df: Historical data (if None, will collect automatically)
            
        Returns:
            Dictionary of model performance metrics
        """
        logger.info("Training ML models...")
        
        if df is None:
            df = self.collect_historical_data()
        
        X, targets = self.prepare_features(df)
        
        performance = {}
        
        # Train service hours predictor
        y_service = targets['service_hours']
        X_train, X_test, y_train, y_test = train_test_split(X, y_service, test_size=0.2, random_state=42)
        
        self.models['service_hours_predictor'].fit(X_train, y_train)
        y_pred = self.models['service_hours_predictor'].predict(X_test)
        
        performance['service_hours'] = {
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred)
        }
        self.is_trained['service_hours_predictor'] = True
        
        # Train maintenance duration predictor
        maintenance_data = df[df['allocated_status'] == 'maintenance']
        if len(maintenance_data) > 50:
            X_maint = maintenance_data[self.feature_columns].fillna(0)
            y_maint = maintenance_data['maintenance_duration_hours']
            
            X_train, X_test, y_train, y_test = train_test_split(X_maint, y_maint, test_size=0.2, random_state=42)
            
            self.models['maintenance_duration_predictor'].fit(X_train, y_train)
            y_pred = self.models['maintenance_duration_predictor'].predict(X_test)
            
            performance['maintenance_duration'] = {
                'mae': mean_absolute_error(y_test, y_pred),
                'r2': r2_score(y_test, y_pred)
            }
            self.is_trained['maintenance_duration_predictor'] = True
        
        # Train failure probability predictor
        y_failure = targets['failure_probability']
        X_train, X_test, y_train, y_test = train_test_split(X, y_failure, test_size=0.2, random_state=42)
        
        self.models['failure_probability_predictor'].fit(X_train, y_train)
        y_pred = self.models['failure_probability_predictor'].predict(X_test)
        
        performance['failure_probability'] = {
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred)
        }
        self.is_trained['failure_probability_predictor'] = True
        
        logger.info("ML model training complete")
        return performance
    
    def predict_service_hours(self, trainset_features: Dict[str, float]) -> float:
        """
        Predict expected service hours for a trainset
        
        Args:
            trainset_features: Dictionary of trainset features
            
        Returns:
            Predicted service hours
        """
        if not self.is_trained['service_hours_predictor']:
            logger.warning("Service hours model not trained, using default")
            return 14.0  # Default service hours
        
        # Prepare feature vector
        feature_vector = np.array([[trainset_features.get(col, 0) for col in self.feature_columns]])
        
        prediction = self.models['service_hours_predictor'].predict(feature_vector)[0]
        return max(0, prediction)  # Ensure non-negative
    
    def predict_maintenance_duration(self, trainset_features: Dict[str, float]) -> float:
        """
        Predict maintenance duration for a trainset
        
        Args:
            trainset_features: Dictionary of trainset features
            
        Returns:
            Predicted maintenance duration in hours
        """
        if not self.is_trained['maintenance_duration_predictor']:
            logger.warning("Maintenance duration model not trained, using default")
            return 8.0  # Default maintenance duration
        
        feature_vector = np.array([[trainset_features.get(col, 0) for col in self.feature_columns]])
        
        prediction = self.models['maintenance_duration_predictor'].predict(feature_vector)[0]
        return max(1, prediction)  # Minimum 1 hour
    
    def predict_failure_probability(self, trainset_features: Dict[str, float]) -> float:
        """
        Predict failure probability for a trainset
        
        Args:
            trainset_features: Dictionary of trainset features
            
        Returns:
            Failure probability (0-1)
        """
        if not self.is_trained['failure_probability_predictor']:
            logger.warning("Failure probability model not trained, using default")
            return 0.05  # Default 5% failure probability
        
        feature_vector = np.array([[trainset_features.get(col, 0) for col in self.feature_columns]])
        
        prediction = self.models['failure_probability_predictor'].predict(feature_vector)[0]
        return max(0, min(1, prediction))  # Clamp to [0, 1]
    
    def update_with_outcome(self, trainset_id: str, features: Dict[str, float], 
                          actual_outcome: Dict[str, float]):
        """
        Update models with actual outcome data (online learning)
        
        Args:
            trainset_id: Trainset identifier
            features: Features used for prediction
            actual_outcome: Actual observed outcomes
        """
        logger.info(f"Recording outcome for {trainset_id}")
        
        # In production, store this data for periodic retraining
        # For now, just log the outcome
        logger.info(f"Actual outcome: {actual_outcome}")
    
    def save_models(self, filepath: str = "models/ml_models.pkl"):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'is_trained': self.is_trained,
            'feature_columns': self.feature_columns
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str = "models/ml_models.pkl"):
        """Load trained models from disk"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.is_trained = model_data['is_trained']
            self.feature_columns = model_data['feature_columns']
            
            logger.info(f"Models loaded from {filepath}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Model file {filepath} not found")
            return False