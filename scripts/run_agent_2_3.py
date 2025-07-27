#!/usr/bin/env python3
"""Agents 2 & 3: Analyze and execute for a specific issue."""

import sys
import os
import json
import threading
import time
from queue import Queue

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent
from utils.utils import get_issue_file_path


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
        plan = agent3.plan(issue, repo_url)
        result_queue.put(("agent3", plan, None))
    except Exception as e:
        result_queue.put(("agent3", None, e))


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
    
    # Queue to collect results from threads
    result_queue = Queue()
    
    # Start both agents in parallel
    print("Starting Agent 2 (feasibility) and Agent 3 (file review) in parallel...")
    
    thread2 = threading.Thread(target=run_agent_2, args=(agent2, issue, repo_url, result_queue))
    thread3 = threading.Thread(target=run_agent_3, args=(agent3, issue, repo_url, result_queue))
    
    thread2.start()
    time.sleep(1)  # Small delay to avoid API overload
    thread3.start()
    
    # Wait for both agents to complete, but always show Agent 2 results first
    print("Waiting for both agents to complete...")
    analysis = None
    plan = None
    agent2_completed = False
    agent3_completed = False
    
    # Wait for Agent 2 to complete first and show results immediately
    print("Waiting for feasibility analysis...")
    analysis = None
    
    while not agent2_completed:
        try:
            agent_type, result, error = result_queue.get(timeout=1)
            if agent_type == "agent2":
                if error:
                    print(f"Agent 2 failed: {error}")
                    print("Sending cancellation message to Agent 3...")
                    agent3.cancel()
                    return
                else:
                    analysis = result
                    agent2_completed = True
                    print(f"Agent 2 completed!")
                    break
            elif agent_type == "agent3":
                # Store Agent 3 result but don't show yet
                if error:
                    print(f"Agent 3 failed: {error}")
                    return
                else:
                    plan = result
                    agent3_completed = True
                    print(f"Agent 3 completed!")
        except:
            if not thread2.is_alive() and not agent2_completed:
                print("Agent 2 thread died without completing")
                return
    
    # Show Agent 2 results immediately
    if analysis:
        print(f"\n=== FEASIBILITY ANALYSIS ===")
        print(f"Feasibility: {analysis.get('feasibility_score', 0)}/100")
        print(f"Complexity: {analysis.get('complexity_score', 0)}/100")
        print(f"Confidence: {analysis.get('confidence', 0)}/100")
    else:
        print("Agent 2 failed to complete")
        return
    
    # Ask user whether to continue with Agent 3
    proceed = input("\nContinue with Agent 3 (planning)? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Sending cancellation message to Agent 3...")
        agent3.cancel()
        return
    
    # Now wait for Agent 3 if it hasn't completed yet
    if not agent3_completed:
        print("Waiting for Agent 3 to complete planning...")
        while not agent3_completed:
            try:
                agent_type, result, error = result_queue.get(timeout=1)
                if agent_type == "agent3":
                    if error:
                        print(f"Agent 3 failed: {error}")
                        return
                    else:
                        plan = result
                        agent3_completed = True
                        print(f"Agent 3 completed plan!")
                        break
            except:
                if not thread3.is_alive():
                    print("Agent 3 thread died without completing")
                    return
    else:
        print("Agent 3 has already completed the plan!")
    
    # Ask for execution approval
    proceed = input("\nExecute this plan? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Stopping. No changes will be made.")
        return
    
    # Execute changes using the same session
    print("Executing...")
    execution_result = agent3.execute(plan, repo_url)
    
    # Show execution results
    if execution_result.get("status") == "changes_made":
        print("Changes executed successfully!")
        print(f"Branch: {execution_result.get('new_branch', 'unknown')}")
        print(f"Commit: {execution_result.get('commit_message', 'unknown')}")
        
        # Show changes
        print("\nChanges made:")
        for change in execution_result.get("changes_made", []):
            print(f"• {change.get('file', 'unknown')}: {change.get('changes', 'unknown')}")
        
        # Ask for push approval
        push_proceed = input("\nPush changes to GitHub? (y/n): ").strip().lower()
        if push_proceed != 'y':
            print("Changes remain local. Not pushing to GitHub.")
            return
        
        # Push to GitHub
        print("Pushing to GitHub...")
        push_result = agent3.push(execution_result, repo_url)
    else:
        print(f"Execution failed: {execution_result.get('reason', 'unknown')}")
    
    print("Workflow completed!")


if __name__ == "__main__":
    main() 