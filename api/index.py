"""Vercel serverless function entry point for GitHub Issues Analyzer."""

import sys
import os

# Add the parent directory to Python path to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Vercel expects the app to be named 'app'
# This should work with Vercel's FastAPI integration 