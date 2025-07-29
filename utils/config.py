"""Configuration and environment variables for the GitHub Issues Analyzer."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Devin API Configuration
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
DEVIN_API_BASE = "https://api.devin.ai/v1"

# Validate API key
if not DEVIN_API_KEY:
    raise ValueError("DEVIN_API_KEY environment variable is not set. Please set it in your .env file.")

# Timeout configurations
SCAN_TIMEOUT = 300  # 5 minutes for repository scanning (deprecated)
TARGETED_ANALYSIS_TIMEOUT = 600  # 10 minutes for targeted analysis (deprecated)
FULL_ANALYSIS_TIMEOUT = 600  # 10 minutes for full repository analysis
EXECUTION_TIMEOUT = 1800  # 30 minutes for execution and pushing (much longer for complex tasks)
ISSUES_FETCH_TIMEOUT = 120  # 2 minutes for fetching issues (should be much faster) 