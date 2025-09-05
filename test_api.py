#!/usr/bin/env python3
"""
API testing script with examples
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8080/api/v1"

def test_connection():
    """Test if API is running"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def get_all_trainsets():
    """Example: Get all trainset data"""
    print("\n📋 Getting all trainsets...")
    
    try:
        response = requests.get(f"{BASE_URL}/trainsets")
        
        if response.status_code == 200:
            trainsets = response.json()
            print(f"✅ Found {len(trainsets)} trainsets")
            
            # Show first trainset as example
            if trainsets:
                first_trainset = trainsets[0]
                print(f"Example trainset: {first_trainset['trainset_id']}")
                print(f"  Status: {first_trainset['current_status']}")
                print(f"  Mileage: {first_trainset['current_mileage']:,} km")
                print(f"  Certificates: {len(first_trainset['fitness_certificates'])}")
                print(f"  Job Cards: {len(first_trainset['job_cards'])}")
            
            return trainsets
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def get_specific_trainset(trainset_id="TS-001"):
    """Example: Get specific trainset"""
    print(f"\n🚂 Getting trainset {trainset_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/trainsets/{trainset_id}")
        
        if response.status_code == 200:
            trainset = response.json()
            print(f"✅ Trainset {trainset_id} details:")
            print(f"  Status: {trainset['current_status']}")
            print(f"  Service Ready: {trainset.get('is_service_ready', 'Unknown')}")
            
            # Show certificates
            for cert in trainset['fitness_certificates']:
                print(f"  📜 {cert['certificate_type']}: {'✅ Valid' if cert['is_valid'] else '❌ Invalid'}")
            
            return trainset
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def run_optimization(service_demand=20):
    """Example: Run optimization"""
    print(f"\n🧠 Running optimization for {service_demand} trainsets...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/optimize",
            params={"service_demand": service_demand}
        )
        
        if response.status_code == 200:
            decisions = response.json()
            print(f"✅ Generated {len(decisions)} decisions")
            
            # Count allocations
            allocations = {}
            for decision in decisions:
                status = decision['recommended_status']
                allocations[status] = allocations.get(status, 0) + 1
            
            print("📊 Allocation Summary:")
            for status, count in allocations.items():
                print(f"  {status.replace('_', ' ').title()}: {count}")
            
            # Show top 3 decisions
            print("\n🏆 Top 3 Priority Trainsets:")
            sorted_decisions = sorted(decisions, key=lambda x: x['priority_score'], reverse=True)
            for i, decision in enumerate(sorted_decisions[:3]):
                print(f"  {i+1}. {decision['trainset_id']} - Score: {decision['priority_score']:.3f}")
                print(f"     Status: {decision['recommended_status']}")
                if decision['reasoning']:
                    print(f"     Reason: {decision['reasoning'][0]}")
            
            return decisions
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def run_simulation():
    """Example: Run what-if simulation"""
    print("\n🎭 Running simulation: Certificate expiry scenario...")
    
    scenario_changes = {
        "scenario_type": "certificate_expiry",
        "modifications": [
            {
                "trainset_id": "TS-003",
                "changes": {
                    "current_status": "maintenance"
                }
            },
            {
                "trainset_id": "TS-007", 
                "changes": {
                    "current_status": "maintenance"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/simulate",
            json=scenario_changes,
            params={"service_demand": 20}
        )
        
        if response.status_code == 200:
            decisions = response.json()
            print(f"✅ Simulation complete: {len(decisions)} decisions")
            
            # Count allocations
            allocations = {}
            for decision in decisions:
                status = decision['recommended_status']
                allocations[status] = allocations.get(status, 0) + 1
            
            print("📊 Simulated Allocation:")
            for status, count in allocations.items():
                print(f"  {status.replace('_', ' ').title()}: {count}")
            
            return decisions
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def add_manual_override():
    """Example: Add manual override"""
    print("\n✋ Adding manual override for TS-005...")
    
    override_data = {
        "status_override": "maintenance",
        "reason": "Operator reported unusual noise during inspection",
        "override_by": "supervisor_001",
        "priority": "high"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/manual-override",
            params={"trainset_id": "TS-005"},
            json=override_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def refresh_data():
    """Example: Refresh data from all sources"""
    print("\n🔄 Refreshing data from all sources...")
    
    try:
        response = requests.post(f"{BASE_URL}/refresh-data")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print(f"📊 Updated {result['trainsets_updated']} trainsets")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def get_system_status():
    """Example: Get system status"""
    print("\n💚 Checking system status...")
    
    try:
        response = requests.get(f"{BASE_URL}/system/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ System Status: {status['status']}")
            print(f"🕐 Timestamp: {status['timestamp']}")
            print(f"📦 Version: {status['version']}")
            
            print("🔧 Components:")
            for component, health in status['components'].items():
                emoji = "✅" if health == "healthy" else "❌"
                print(f"  {emoji} {component}: {health}")
            
            return status
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Run all API tests"""
    print("🧪 KMRL API Testing Suite")
    print("=" * 40)
    
    # Test connection
    if not test_connection():
        print("\n💡 Make sure to start the API first:")
        print("   python run_local.py")
        return
    
    # Wait a moment for system to be ready
    time.sleep(1)
    
    # Run tests
    get_system_status()
    refresh_data()
    get_all_trainsets()
    get_specific_trainset("TS-001")
    add_manual_override()
    run_optimization(service_demand=20)
    run_simulation()
    
    print("\n🎉 All API tests completed!")
    print("\n💡 Try the interactive dashboard at: http://localhost:8050")

if __name__ == "__main__":
    main()