#!/usr/bin/env python3
"""Agents 2 & 3: Analyze and execute for a specific issue."""

import sys
import json
import os
import threading
import time
import signal
from queue import Queue

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.utils import get_cache_key
from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent


def run_agent_2(agent2, issue, repo_url, result_queue):
    """Run Agent 2 in a separate thread."""
    try:
        analysis = agent2.analyze_issue_feasibility(issue, repo_url)
        result_queue.put(("agent2", analysis, None))
    except Exception as e:
        result_queue.put(("agent2", None, e))


def run_agent_3(agent3, issue, repo_url, result_queue):
    """Run Agent 3 in a separate thread."""
    try:
        review = agent3.review_files_and_plan(issue, repo_url)
        result_queue.put(("agent3", review, None))
    except Exception as e:
        result_queue.put(("agent3", None, e))


def run_agents_parallel(issue, repo_url):
    """Run Agent 2 and Agent 3 in parallel using threads."""
    agent2 = FeasibilityAnalyzerAgent()
    agent3 = FileReviewerAgent()
    
    # Queue to collect results from threads
    result_queue = Queue()
    
    # Start both agents in parallel
    print("Starting Agent 2 (feasibility analysis) and Agent 3 (file review) in parallel...")
    
    thread2 = threading.Thread(target=run_agent_2, args=(agent2, issue, repo_url, result_queue))
    thread3 = threading.Thread(target=run_agent_3, args=(agent3, issue, repo_url, result_queue))
    
    thread2.start()
    time.sleep(1)  # Small delay to avoid API overload
    thread3.start()
    
    # Wait for Agent 2 to complete first (feasibility analysis)
    print("Waiting for feasibility analysis...")
    analysis = None
    review = None
    agent2_error = None
    agent3_error = None
    
    while True:
        try:
            agent_type, result, error = result_queue.get(timeout=1)
            if agent_type == "agent2":
                if error:
                    agent2_error = error
                    print(f"Agent 2 failed: {error}")
                    print("Sending cancellation message to Agent 3...")
                    agent3.cancel()  # This sends a message to the Devin session
                    return {"status": "failed", "reason": f"Agent 2 failed: {error}"}
                else:
                    analysis = result
                    print(f"Agent 2 completed!")
                    break
        except:
            # Check if Agent 2 thread is still running
            if not thread2.is_alive():
                break
    
    print(f"Feasibility: {analysis.get('feasibility_score', 0)}/100")
    print(f"Complexity: {analysis.get('complexity_score', 0)}/100")
    print(f"Confidence: {analysis.get('confidence', 0)}/100")
    
    # Ask user whether to let Agent 3 continue
    proceed = input("\nAgent 3 is still working on file review. Let it continue? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Sending cancellation message to Agent 3...")
        agent3.cancel()  # This sends a message to the Devin session
        return {"status": "cancelled", "reason": "User cancelled after feasibility analysis"}
    
    # Wait for Agent 3 to complete
    print("Waiting for file review to complete...")
    while True:
        try:
            agent_type, result, error = result_queue.get(timeout=1)
            if agent_type == "agent3":
                if error:
                    agent3_error = error
                    print(f"Agent 3 failed: {error}")
                    return {"status": "failed", "reason": f"Agent 3 failed: {error}"}
                else:
                    review = result
                    print(f"Agent 3 completed!")
                    break
        except:
            # Check if Agent 3 thread is still running
            if not thread3.is_alive():
                break
    
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
    
    # Run both agents in parallel
    result = run_agents_parallel(issue, repo_url)
    
    if result.get("status") == "completed":
        print("Done!")
    else:
        print(f"Stopped: {result.get('reason')}")


if __name__ == "__main__":
    main() 