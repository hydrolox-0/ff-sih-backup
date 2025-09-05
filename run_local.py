#!/usr/bin/env python3
"""
Local development runner for KMRL Induction System
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi, uvicorn, pandas, numpy, plotly, dash
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server on http://localhost:8080")
    return subprocess.Popen([
        sys.executable, "main.py"
    ])

def start_dashboard():
    """Start the Dash dashboard"""
    print("📊 Starting dashboard on http://localhost:8050")
    return subprocess.Popen([
        sys.executable, "dashboard/app.py"
    ])

def main():
    print("🚇 KMRL Trainset Induction System - Local Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    
    try:
        # Start API server
        api_process = start_api_server()
        time.sleep(3)  # Give API time to start
        
        # Start dashboard
        dashboard_process = start_dashboard()
        time.sleep(2)  # Give dashboard time to start
        
        print("\n🎉 System is running!")
        print("📡 API: http://localhost:8080")
        print("📊 Dashboard: http://localhost:8050")
        print("📚 API Docs: http://localhost:8080/docs")
        print("\nPress Ctrl+C to stop all services")
        
        # Open browser
        webbrowser.open("http://localhost:8050")
        
        # Wait for processes
        api_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        if 'api_process' in locals():
            api_process.terminate()
        if 'dashboard_process' in locals():
            dashboard_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()