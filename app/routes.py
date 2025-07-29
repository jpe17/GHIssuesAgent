"""Simple FastAPI routes for GitHub Issues Agent frontend."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import json
import os
import sys
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import get_issue_file_path

router = APIRouter()

# Simple request models
class RepoRequest(BaseModel):
    repo_url: str

class IssueRequest(BaseModel):
    repo_url: str
    issue_id: str

class MultiIssueRequest(BaseModel):
    repo_url: str
    issue_ids: list[str]

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main frontend page."""
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@router.post("/api/fetch-issues")
async def fetch_issues(request: RepoRequest):
    """Fetch issues from a repository."""
    try:
        print(f"🔄 Starting fetch for: {request.repo_url}")
        
        # Use the issue fetcher agent directly
        agent = IssueFetcherAgent()
        issues_data = agent.fetch_issues(request.repo_url)
        
        # Convert to the expected format
        issues = []
        for issue_data in issues_data:
            issues.append({
                "id": str(issue_data.get('number', '')),
                "title": issue_data.get('title', 'No title'),
                "state": issue_data.get('state', 'open'),
                "body": issue_data.get('body', ''),
                "created_at": issue_data.get('created_at', ''),
                "updated_at": issue_data.get('updated_at', '')
            })
        
        # Sort by issue number
        issues.sort(key=lambda x: int(x["id"]))
        
        print(f"✅ Successfully fetched {len(issues)} issues")
        return {"issues": issues}
            
    except Exception as e:
        print(f"❌ Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

def analyze_single_issue(repo_url: str, issue_id: str) -> dict:
    """Analyze a single issue (for parallel processing)."""
    import threading
    thread_id = threading.current_thread().ident
    
    try:
        print(f"🎯 Starting analysis for issue #{issue_id} (Thread: {thread_id})")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Run Agents 2 & 3 in parallel using asyncio
        print(f"🚀 Creating Agent 2 & 3 sessions for issue #{issue_id} (Thread: {thread_id})")
        
        async def run_parallel_analysis():
            loop = asyncio.get_event_loop()
            
            # Start both agents simultaneously
            agent2_task = loop.run_in_executor(None, lambda: FeasibilityAnalyzerAgent().analyze_issue_feasibility(issue, repo_url))
            agent3_task = loop.run_in_executor(None, lambda: PlanAgent().review_files_and_plan(issue, repo_url))
            
            # Wait for both to complete
            analysis, plan = await asyncio.gather(agent2_task, agent3_task)
            return analysis, plan
        
        # Run the async function in the current thread
        try:
            # Create new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            analysis, plan = loop.run_until_complete(run_parallel_analysis())
            
        except Exception as e:
            print(f"❌ Parallel analysis failed for issue #{issue_id}: {str(e)}")
            return {"issue_id": issue_id, "error": f"Parallel analysis failed: {str(e)}"}
        
        print(f"✅ Agent 2 completed for issue #{issue_id} (Thread: {thread_id})")
        print(f"✅ Agent 3 completed for issue #{issue_id} (Thread: {thread_id})")
        print(f"🎉 Analysis completed for issue #{issue_id} (Thread: {thread_id})")
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "analysis": analysis,
            "plan": plan
        }
    except Exception as e:
        print(f"💥 Analysis failed for issue #{issue_id} (Thread: {thread_id}): {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze a specific issue."""
    try:
        print(f"🎯 Starting analysis for issue #{request.issue_id}")
        
        # Run the analysis directly
        result = analyze_single_issue(request.repo_url, request.issue_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "issue_id": request.issue_id,
            "status": "completed",
            "analysis": result.get('analysis'),
            "plan": result.get('plan')
        }
        
    except Exception as e:
        print(f"❌ Analysis failed for issue #{request.issue_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analyze-multiple-issues")
async def analyze_multiple_issues(request: MultiIssueRequest):
    """Analyze multiple issues in parallel."""
    try:
        print(f"🔍 MULTIPLE ANALYSIS STARTED: {len(request.issue_ids)} issues: {request.issue_ids}")
        print(f"📍 Repo URL: {request.repo_url}")
        
        # Run all issues in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(request.issue_ids), 5)) as executor:
            print(f"🏭 Created ThreadPoolExecutor with {min(len(request.issue_ids), 5)} workers")
            
            futures = []
            for issue_id in request.issue_ids:
                print(f"📤 Submitting analysis task for issue #{issue_id}")
                future = executor.submit(analyze_single_issue, request.repo_url, issue_id)
                futures.append(future)
            
            print(f"📊 Submitted {len(futures)} tasks to executor")
            
            # Collect results as they complete
            results = []
            for i, future in enumerate(futures):
                try:
                    print(f"⏳ Waiting for result {i+1}/{len(futures)}")
                    result = future.result()
                    print(f"✅ Got result for issue: {result.get('issue_id', 'unknown')}")
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error getting result {i+1}: {str(e)}")
                    results.append({"error": str(e)})
        
        print(f"🎉 MULTIPLE ANALYSIS COMPLETED: {len(results)} results")
        return {"results": results}
        
    except Exception as e:
        print(f"💥 MULTIPLE ANALYSIS FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def execute_single_issue(repo_url: str, issue_id: str) -> dict:
    """Execute a single issue."""
    try:
        print(f"🚀 Starting execution for issue #{issue_id}")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Get plan first
        print(f"📋 Getting plan for issue #{issue_id}")
        agent3 = PlanAgent()
        plan = agent3.review_files_and_plan(issue, repo_url)
        
        if not plan:
            return {"issue_id": issue_id, "error": "No plan available"}
        
        # Execute the plan
        print(f"⚡ Executing plan for issue #{issue_id}")
        agent4 = ExecutorAgent()
        push_result = agent4.execute_and_push(plan, repo_url)
        
        print(f"✅ Execution completed for issue #{issue_id}")
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "result": push_result
        }
        
    except Exception as e:
        print(f"❌ Execution failed for issue #{issue_id}: {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/execute")
async def execute_changes(request: IssueRequest):
    """Execute the plan and push changes."""
    try:
        print(f"🚀 Starting execution for issue #{request.issue_id}")
        
        # Load cached analysis and plan
        issue_file = get_issue_file_path(request.repo_url, request.issue_id)
        
        if not os.path.exists(issue_file):
            raise HTTPException(status_code=404, detail="Issue analysis not found. Please analyze the issue first.")
        
        with open(issue_file, 'r') as f:
            cached_data = json.load(f)
        
        plan_data = cached_data.get('plan', {})
        if not plan_data:
            raise HTTPException(status_code=400, detail="No plan found for this issue.")
        
        # Execute the plan
        result = execute_single_issue(request.repo_url, request.issue_id)
        
        return {
            "status": "success",
            "message": f"Execution completed for issue #{request.issue_id}",
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Error executing changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute changes: {str(e)}")

@router.post("/api/execute-multiple-issues")
async def execute_multiple_issues(request: MultiIssueRequest):
    """Execute multiple issues in parallel."""
    try:
        print(f"🚀 MULTIPLE EXECUTION STARTED: {len(request.issue_ids)} issues: {request.issue_ids}")
        print(f"📍 Repo URL: {request.repo_url}")
        
        # Run all issues in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(request.issue_ids), 3)) as executor:
            print(f"🏭 Created ThreadPoolExecutor with {min(len(request.issue_ids), 3)} workers")
            
            futures = []
            for i, issue_id in enumerate(request.issue_ids):
                print(f"📤 Submitting execution task for issue #{issue_id}")
                future = executor.submit(execute_single_issue, request.repo_url, issue_id)
                futures.append(future)
                
                # Add delay between submissions to avoid rate limiting
                if i < len(request.issue_ids) - 1:  # Don't sleep after the last one
                    print(f"⏸️ Waiting 3 seconds before next execution submission...")
                    time.sleep(3)  # 3 second delay between executions
            
            print(f"📊 Submitted {len(futures)} tasks to executor")
            
            # Collect results as they complete
            results = []
            for i, future in enumerate(futures):
                try:
                    print(f"⏳ Waiting for execution result {i+1}/{len(futures)}")
                    result = future.result()
                    print(f"✅ Got execution result for issue: {result.get('issue_id', 'unknown')}")
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error getting execution result {i+1}: {str(e)}")
                    results.append({"error": str(e)})
        
        print(f"🎉 MULTIPLE EXECUTION COMPLETED: {len(results)} results")
        return {"results": results}
        
    except Exception as e:
        print(f"💥 MULTIPLE EXECUTION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Dependency for Devin session (placeholder)
def get_devin_session():
    """Get the Devin API session."""
    return None
