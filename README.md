# Kochi Metro Trainset Induction Decision Support System

## Overview
An integrated, algorithm-driven platform for optimizing daily trainset allocation decisions across 25 four-car trainsets, considering fitness certificates, maintenance schedules, branding priorities, mileage balancing, cleaning slots, and stabling geometry.

## Key Features
- Real-time data ingestion from multiple sources (Maximo, IoT sensors, manual inputs)
- Multi-objective optimization engine
- Explainable decision reasoning
- What-if simulation capabilities
- Machine learning feedback loops
- Conflict detection and alerting

## Architecture
```
├── data_ingestion/     # Connectors for Maximo, IoT, manual inputs
├── optimization/       # Core decision engine and algorithms
├── simulation/         # What-if scenario modeling
├── ml_feedback/        # Learning from historical outcomes
├── api/               # REST API for system integration
├── dashboard/         # Web interface for operators
└── config/            # System configuration and rules
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure data sources in `config/sources.yaml`
3. Run the system: `python main.py`
4. Access dashboard at `http://localhost:8080`