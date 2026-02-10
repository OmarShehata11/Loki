#!/usr/bin/env python3
"""
FastAPI server for Loki IDS.
Runs separately from packet processing for better isolation and performance.
"""
import uvicorn
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.main import app

if __name__ == "__main__":
    print("======================================================"
)
    print("         Loki IDS - API Server")
    print("======================================================")
    print("[*] Starting API Server on http://localhost:8080")
    print("[*] Dashboard: http://localhost:8080")
    print("[*] API Documentation: http://localhost:8080/docs")
    print("======================================================")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
