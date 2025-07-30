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

# Timeout configurations for different operations
ISSUES_FETCH_TIMEOUT = 120     # 2 minutes for fetching issues
FULL_ANALYSIS_TIMEOUT = 900    # 15 minutes for analysis and planning (increased)
EXECUTION_TIMEOUT = 1800       # 30 minutes for execution and PR creation

# Rate limiting configuration
MIN_SECONDS_BETWEEN_CALLS = 5  # Minimum seconds between API calls 