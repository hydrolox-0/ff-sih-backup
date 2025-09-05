# 🚇 KMRL Induction System - Local Setup Guide

## 📋 Prerequisites

- Python 3.8+ installed
- Git (to clone/download the project)
- Web browser

## 🚀 Quick Start (3 steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the System
```bash
python run_local.py
```

### Step 3: Open Your Browser
The system will automatically open the dashboard at:
- **Dashboard**: http://localhost:8050
- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 🧪 Test the APIs

Run the test script to see all endpoints in action:
```bash
python test_api.py
```

## 📡 API Endpoints Reference

### 1. Get System Status
```bash
curl http://localhost:8080/api/v1/system/status
```

### 2. Get All Trainsets
```bash
curl http://localhost:8080/api/v1/trainsets
```

### 3. Get Specific Trainset
```bash
curl http://localhost:8080/api/v1/trainsets/TS-001
```

### 4. Run Optimization
```bash
curl -X POST "http://localhost:8080/api/v1/optimize?service_demand=20"
```

### 5. Add Manual Override
```bash
curl -X POST "http://localhost:8080/api/v1/manual-override?trainset_id=TS-005" \
  -H "Content-Type: application/json" \
  -d '{
    "status_override": "maintenance",
    "reason": "Operator reported issue",
    "override_by": "supervisor_001"
  }'
```

### 6. Run What-If Simulation
```bash
curl -X POST "http://localhost:8080/api/v1/simulate?service_demand=20" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_type": "emergency_maintenance",
    "modifications": [
      {
        "trainset_id": "TS-003",
        "changes": {
          "current_status": "maintenance"
        }
      }
    ]
  }'
```

### 7. Refresh Data
```bash
curl -X POST http://localhost:8080/api/v1/refresh-data
```

### 8. Remove Manual Override
```bash
curl -X DELETE http://localhost:8080/api/v1/manual-override/TS-005
```

## 🎛️ Using the Dashboard

1. **Control Panel**: Adjust service demand (15-25 trainsets)
2. **Optimize Button**: Generate new induction decisions
3. **Refresh Button**: Update data from all sources
4. **Status Cards**: See fleet overview at a glance
5. **Charts**: Visual allocation and priority analysis
6. **Decision Table**: Detailed reasoning for each trainset

## 🔧 Troubleshooting

### Port Already in Use
If you get port errors:
```bash
# Kill processes on ports 8080 and 8050
netstat -ano | findstr :8080
netstat -ano | findstr :8050
# Then kill the process IDs shown
```

### Missing Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### API Not Responding
1. Check if `python run_local.py` is still running
2. Wait 10-15 seconds for startup
3. Check logs in the terminal

## 📊 Sample Data

The system comes with mock data for 25 trainsets:
- **TS-001** to **TS-025**: Four-car trainsets
- **Mock certificates**: Rolling stock, signalling, telecom
- **Sample job cards**: From IBM Maximo simulation
- **Branding contracts**: Advertiser exposure tracking

## 🎯 Key Features to Try

1. **Run Optimization**: See how the algorithm allocates trainsets
2. **Add Override**: Force a trainset to maintenance and see impact
3. **What-If Scenarios**: Simulate certificate expiry or equipment failure
4. **Real-time Updates**: Dashboard refreshes automatically
5. **Explainable Decisions**: Each allocation shows reasoning

## 🚀 Next Steps

- Customize weights in `config/settings.yaml`
- Add real data connectors in `data_ingestion/`
- Extend scenarios in `simulation/scenario_engine.py`
- Deploy with Docker using `docker-compose up`

## 💡 Tips

- Use the interactive API docs at http://localhost:8080/docs
- Check the terminal for detailed logs
- The system auto-refreshes data every 30 seconds
- All decisions include explainable reasoning