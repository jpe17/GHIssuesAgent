#!/usr/bin/env python3
"""Agent 2: Analyze feasibility for a specific issue."""

import sys
import os
import json

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from utils.utils import get_issue_file_path


def main():
    """Run Agent 2 for feasibility analysis on a specific issue."""
    # Get repo URL and issue ID
    if len(sys.argv) < 3:
        repo_url = input("Repo URL: ").strip()
        issue_id = input("Issue ID: ").strip()
    else:
        repo_url = sys.argv[1]
        issue_id = sys.argv[2]
    
    if not repo_url or not issue_id:
        print("Need repo URL and issue ID")
        return
    
    try:
        issue_id = int(issue_id)
    except ValueError:
        print("Issue ID must be a number")
        return
    
    # Get issue from cache
    issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
    
    if not os.path.exists(issue_file_path):
        print(f"Issue #{issue_id} not found. Run run_agent_1.py first.")
        return
    
    with open(issue_file_path, 'r') as f:
        issue = json.load(f)
    
    print(f"Analyzing issue #{issue_id}: {issue.get('title')}")
    
    # Initialize agent and analyze
    agent2 = FeasibilityAnalyzerAgent()
    
    try:
        analysis = agent2.analyze_issue_feasibility(issue, repo_url)
        
        # Show key results
        print(f"\nFeasibility: {analysis.get('feasibility_score', 0)}/100")
        print(f"Complexity: {analysis.get('complexity_score', 0)}/100")
        print(f"Confidence: {analysis.get('confidence', 0)}/100")
        
        # Show effort estimate
        effort = analysis.get('effort_estimation', {})
        if effort.get('hours'):
            print(f"Estimated hours: {effort['hours']}")
        
        # Show files to modify
        tech = analysis.get('technical_analysis', {})
        files = tech.get('estimated_files', [])
        if files:
            print(f"Files to modify: {', '.join(files)}")
        
        print("Analysis completed!")
        
    except Exception as e:
        print(f"Analysis failed: {e}")


if __name__ == "__main__":
    main()