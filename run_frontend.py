#!/usr/bin/env python3
"""Startup script for the GitHub Issues Agent frontend."""

import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting GitHub Issues Agent Frontend...")
    print("📱 Open your browser to: http://localhost:8844")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8844,
        reload=True,
        log_level="info"
    ) 