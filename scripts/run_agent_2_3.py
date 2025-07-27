#!/usr/bin/env python3
"""Agents 2 & 3: Analyze and execute for a specific issue."""

import sys
import os
import json

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent
from utils.utils import get_issue_file_path


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
    issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
    
    if not os.path.exists(issue_file_path):
        print(f"Issue #{issue_id} not found. Run run_agent_1.py first.")
        return
    
    with open(issue_file_path, 'r') as f:
        issue = json.load(f)
    
    print(f"Working on issue #{issue_id}: {issue.get('title')}")
    
    # Initialize agents
    agent2 = FeasibilityAnalyzerAgent()
    agent3 = FileReviewerAgent()
    
    # Step 1: Analyze feasibility
    print("\n=== Step 1: Analyzing feasibility ===")
    try:
        analysis = agent2.analyze_issue_feasibility(issue, repo_url)
        print(f"✅ Feasibility: {analysis.get('feasibility_score', 0)}/100")
        print(f"✅ Complexity: {analysis.get('complexity_score', 0)}/100")
        print(f"✅ Confidence: {analysis.get('confidence', 0)}/100")
    except Exception as e:
        print(f"❌ Feasibility analysis failed: {e}")
        return
    
    # Ask user whether to continue
    proceed = input("\nContinue with file review? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Stopping workflow.")
        return
    
    # Step 2: Review files and create plan
    print("\n=== Step 2: Reviewing files and creating plan ===")
    try:
        review = agent3.review_files_and_plan(issue, repo_url)
        print("✅ File review completed!")
        
        # Show plan
        print("\nPlan:")
        for step in review.get("action_plan", []):
            print(f"• {step.get('description', 'No description')}")
    except Exception as e:
        print(f"❌ File review failed: {e}")
        return
    
    # Ask for execution approval
    proceed = input("\nExecute changes? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Stopping workflow.")
        return
    
    # Step 3: Execute changes
    print("\n=== Step 3: Executing changes ===")
    try:
        execution_result = agent3.execute_changes(review, repo_url, user_approval=True)
        
        if execution_result.get("status") == "changes_made":
            print("✅ Changes executed successfully!")
            print(f"Branch: {execution_result.get('new_branch', 'unknown')}")
            print(f"Commit: {execution_result.get('commit_message', 'unknown')}")
            
            # Show changes
            print("\nChanges made:")
            for change in execution_result.get("changes_made", []):
                print(f"• {change.get('file', 'unknown')}: {change.get('changes', 'unknown')}")
        else:
            print(f"❌ Execution failed: {execution_result.get('reason', 'unknown')}")
            return
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return
    
    # Ask for push approval
    push_proceed = input("\nPush changes to GitHub? (y/n): ").strip().lower()
    if push_proceed != 'y':
        print("✅ Changes remain local. Not pushing to GitHub.")
        return
    
    # Step 4: Push to GitHub
    print("\n=== Step 4: Pushing to GitHub ===")
    try:
        push_result = agent3.push_to_github(execution_result, repo_url, user_approval=True)
        
        if push_result.get("status") == "completed":
            print("✅ Successfully pushed to GitHub!")
            print(f"URL: {push_result.get('push_url', 'unknown')}")
        else:
            print(f"❌ Push failed: {push_result.get('reason', 'unknown')}")
    except Exception as e:
        print(f"❌ Push failed: {e}")
    
    print("\n🎉 Workflow completed!")


if __name__ == "__main__":
    main() 