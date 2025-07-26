"""Configuration and environment variables for the GitHub Issues Analyzer."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Devin API Configuration
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
DEVIN_API_BASE = "https://api.devin.ai/v1"

# Validation
if not DEVIN_API_KEY:
    raise ValueError("DEVIN_API_KEY environment variable is required")

# Timeout configurations
SCAN_TIMEOUT = 180  # 3 minutes for repository scanning
TARGETED_ANALYSIS_TIMEOUT = 300  # 5 minutes for targeted analysis
FULL_ANALYSIS_TIMEOUT = 600  # 10 minutes for full repository analysis
ISSUES_FETCH_TIMEOUT = 120  # 2 minutes for fetching issues 