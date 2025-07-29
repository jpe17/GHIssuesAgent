#!/usr/bin/env python3
"""Unified script to run all agents: fetch issues, analyze feasibility, and execute changes."""

import sys
import os
import json
import threading
import time
from queue import Queue

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import cancel_session, get_issue_file_path


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
        plan = agent3.review_files_and_plan(issue, repo_url)
        result_queue.put(("agent3", plan, None))
    except Exception as e:
        result_queue.put(("agent3", None, e))


def check_cache_exists(repo_url):
    """Check if cache exists for the repository."""
    repo_key = repo_url.replace("https://github.com/", "").replace("/", "_")
    cache_dir = os.path.join("cache", "issues", repo_key)
    return os.path.exists(cache_dir) and len(os.listdir(cache_dir)) > 0


def fetch_and_display_issues(repo_url):
    """Phase 1: Fetch issues and display them for selection."""
    print(f"📋 Fetching issues from {repo_url}...")
    
    # Fetch issues if needed
    if not check_cache_exists(repo_url):
        agent1 = IssueFetcherAgent()
        issues = agent1.fetch_and_cache_issues(repo_url)
        if not issues:
            print("❌ Failed to fetch issues")
            return None
    else:
        print("✅ Using cached issues")
    
    # Load and display issues
    repo_key = repo_url.replace("https://github.com/", "").replace("/", "_")
    cache_dir = os.path.join("cache", "issues", repo_key)
    
    if not os.path.exists(cache_dir):
        print("❌ No cached issues found")
        return None
    
    issues = []
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            # Extract issue number from filename (e.g., "issue_3.json" -> "3")
            issue_id = filename.replace('.json', '').replace('issue_', '')
            file_path = os.path.join(cache_dir, filename)
            with open(file_path, 'r') as f:
                issue_data = json.load(f)
                issues.append((issue_id, issue_data))
    
    # Sort by issue number
    issues.sort(key=lambda x: int(x[0]))
    
    print(f"\n📋 Found {len(issues)} issues:")
    print("-" * 80)
    for issue_id, issue_data in issues:
        title = issue_data.get('title', 'No title')
        state = issue_data.get('state', 'unknown')
        print(f"#{issue_id:<4} [{state:<8}] {title}")
    print("-" * 80)
    
    return issues


def run_agents_on_issue(repo_url, issue_id):
    """Phase 2: Run agents 2 and 3 on a specific issue."""
    # Load issue
    issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
    if not os.path.exists(issue_file_path):
        print(f"❌ Issue #{issue_id} not found")
        return
    
    with open(issue_file_path, 'r') as f:
        issue = json.load(f)
    
    print(f"\n🎯 Processing Issue #{issue_id}: {issue.get('title')}")
    
    # Run Agents 2 & 3 in parallel
    agent2 = FeasibilityAnalyzerAgent()
    agent3 = PlanAgent()  # Remove the api_token parameter
    result_queue = Queue()
    
    thread2 = threading.Thread(target=run_agent_2, args=(agent2, issue, repo_url, result_queue))
    thread3 = threading.Thread(target=run_agent_3, args=(agent3, issue, repo_url, result_queue))
    
    thread2.start()
    time.sleep(1)
    thread3.start()
    
    # Wait for results
    analysis = None
    plan = None
    agent2_completed = False
    agent3_completed = False
    
    # Wait for both agents to complete
    while not (agent2_completed and agent3_completed):
        try:
            agent_type, result, error = result_queue.get(timeout=1)
            if agent_type == "agent2":
                if error:
                    print(f"❌ Agent 2 failed: {error}")
                    if agent3._current_session_id:
                        cancel_session(agent3._current_session_id)
                    return
                analysis = result
                agent2_completed = True
            elif agent_type == "agent3":
                if error:
                    print(f"❌ Agent 3 failed: {error}")
                    return
                plan = result
                agent3_completed = True
        except:
            if not thread2.is_alive() and not agent2_completed:
                print("❌ Agent 2 failed")
                return
            if not thread3.is_alive() and not agent3_completed:
                print("❌ Agent 3 failed")
                return
    
    # Show both results together
    print(f"\n📊 Feasibility Analysis:")
    print(f"   Score: {analysis.get('feasibility_score', 0)}/100")
    if analysis.get('feasibility_score', 0) < 50:
        print("   ⚠️  Low feasibility score")
    
    print(f"\n📋 Implementation Plan:")
    print(f"   Summary: {plan.get('summary', 'No summary available')}")
    print(f"   Estimated Effort: {plan.get('estimated_effort', 'Unknown')}")
    
    if plan.get('risks'):
        print(f"   ⚠️  Risks: {', '.join(plan.get('risks', []))}")
    
    if plan.get('action_plan'):
        print(f"   📝 Action Plan:")
        for step in plan.get('action_plan', []):
            print(f"     Step {step.get('step', '?')}: {step.get('description', 'No description')}")
            if step.get('files'):
                print(f"       Files: {', '.join(step.get('files', []))}")
    
    print("\n" + "="*80)
    print("🚀 Execute and push changes?")
    print("1. Yes, execute and push")
    print("2. Cancel")
    
    while True:
        choice = input("Enter choice (1/2): ").strip()
        if choice == "1":
            # Execute and push immediately
            print("⚡ Executing and pushing...")
            agent4 = ExecutorAgent()
            push_result = agent4.execute_and_push(plan, repo_url)
            if push_result.get("status") == "success":
                print(f"✅ Pushed successfully!")
                pr_url = push_result.get("pr_url")
                if pr_url:
                    print(f"🔗 Pull Request: {pr_url}")
                else:
                    print("ℹ️  PR URL not found in session messages")
            else:
                session_result = push_result.get("session_result", {})
                if session_result.get("error") == "api_errors":
                    print(f"⚠️  API connection issues detected")
                    print(f"   Session ID: {session_result.get('session_id')}")
                    print(f"   The session might still be running on the Devin frontend.")
                    print(f"   Check the frontend to see if the execution completed successfully.")
                else:
                    print(f"❌ Push failed: {push_result.get('reason', 'Unknown')}")
            break
        elif choice == "2":
            return
        else:
            print("❌ Please enter 1 or 2")
    



def main():
    """Run the complete agent workflow with two-phase approach."""
    # Get repo URL
    if len(sys.argv) < 2:
        repo_url = input("Repo URL: ").strip()
    else:
        repo_url = sys.argv[1]
    
    if not repo_url:
        print("❌ Need repo URL")
        return
    
    # Phase 1: Fetch and display issues
    issues = fetch_and_display_issues(repo_url)
    if not issues:
        return
    
    # Phase 2: Choose issue and run agents
    while True:
        try:
            issue_id = input(f"\n🎯 Choose issue number (1-{len(issues)}): ").strip()
            if not issue_id:
                print("❌ Please enter an issue number")
                continue
            
            issue_id = int(issue_id)
            if 1 <= issue_id <= len(issues):
                selected_issue_id = str(issues[issue_id - 1][0])
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(issues)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return
    
    # Run agents on selected issue
    run_agents_on_issue(repo_url, selected_issue_id)


if __name__ == "__main__":
    main() 