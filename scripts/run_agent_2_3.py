#!/usr/bin/env python3
"""Agents 2 & 3: Analyze and execute for a specific issue."""

import sys
import json
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.utils import get_cache_key

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent


def run_agents_sequential(issue, repo_url):
    """Run Agent 2 and Agent 3 sequentially."""
    agent2 = FeasibilityAnalyzerAgent()
    agent3 = FileReviewerAgent()
    
    # Run Agent 2 first (feasibility analysis)
    print("Starting Agent 2 (feasibility analysis)...")
    analysis = agent2.analyze_issue_feasibility(issue, repo_url)
    
    print(f"Feasibility: {analysis.get('feasibility_score', 0)}/100")
    print(f"Complexity: {analysis.get('complexity_score', 0)}/100")
    print(f"Confidence: {analysis.get('confidence', 0)}/100")
    
    # Ask user whether to continue with Agent 3
    proceed = input("\nContinue with file review? (y/n): ").strip().lower()
    if proceed != 'y':
        return {"status": "cancelled", "reason": "User cancelled after feasibility analysis"}
    
    # Run Agent 3 (file review)
    print("Starting Agent 3 (file review)...")
    review = agent3.review_files_and_plan(issue, repo_url)
    
    # Show plan
    print("\nPlan:")
    for step in review.get("action_plan", []):
        print(f"• {step.get('description', 'No description')}")
    
    # Ask for execution approval
    proceed = input("\nExecute changes? (y/n): ").strip().lower()
    if proceed != 'y':
        return {"status": "cancelled", "reason": "User cancelled execution"}
    
    # Execute changes
    print("Executing...")
    result = agent3.execute_changes(review, repo_url, user_approval=True)
    
    return {
        "status": "completed",
        "analysis": analysis,
        "review": review,
        "execution": result
    }


def main():
    """Run Agents 2 & 3 for a specific issue."""
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
    agent1 = IssueFetcherAgent()
    issue = agent1.get_single_issue(repo_url, issue_id)
    
    if not issue:
        print(f"Issue #{issue_id} not found. Run run_agent_1.py first.")
        return
    
    print(f"Working on issue #{issue_id}: {issue.get('title')}")
    
    # Run both agents sequentially
    result = run_agents_sequential(issue, repo_url)
    
    if result.get("status") == "completed":
        print("Done!")
    else:
        print(f"Stopped: {result.get('reason')}")


if __name__ == "__main__":
    main() 