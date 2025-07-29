"""Simple FastAPI routes for GitHub Issues Agent frontend with simplified rate limiting."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import get_issue_file_path

router = APIRouter()

# Sequential lock for Devin API calls - only 1 at a time
devin_api_lock = threading.Lock()

# Request models
class RepoRequest(BaseModel):
    repo_url: str

class IssueRequest(BaseModel):
    repo_url: str
    issue_id: str

class MultiIssueRequest(BaseModel):
    repo_url: str
    issue_ids: list[str]

def safe_devin_api_call(func, *args, **kwargs):
    """Make a Devin API call - SEQUENTIAL ONLY to avoid rate limits."""
    with devin_api_lock:  # Only 1 Devin API call at a time across all threads
        for attempt in range(3):
            try:
                print(f"🔄 Making Devin API call (attempt {attempt + 1}/3)")
                result = func(*args, **kwargs)
                print(f"✅ Devin API call successful")
                return result
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e) or "devin.ai" in str(e):
                    wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s
                    print(f"⚠️  Devin API rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt == 2:  # Last attempt
                        raise Exception(f"Devin API rate limited after 3 attempts: {str(e)}")
                else:
                    raise
        
def safe_github_api_call(func, *args, **kwargs):
    """Make a GitHub API call with basic retry."""
    for attempt in range(2):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print(f"⚠️  GitHub API rate limited, waiting 5s...")
                time.sleep(5)
            else:
                raise

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main frontend page."""
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@router.post("/api/fetch-issues")
async def fetch_issues(request: RepoRequest):
    """Fetch issues from a repository."""
    try:
        print(f"🔄 Fetching issues from: {request.repo_url}")
        
        agent = IssueFetcherAgent()
        issues_data = safe_github_api_call(agent.fetch_and_cache_issues, request.repo_url)
        
        # Convert to frontend format
        issues = [{
            "id": str(issue_data.get('number', '')),
            "title": issue_data.get('title', 'No title'),
            "state": issue_data.get('state', 'open'),
            "body": issue_data.get('body', ''),
            "created_at": issue_data.get('created_at', ''),
            "updated_at": issue_data.get('updated_at', '')
        } for issue_data in issues_data]
        
        issues.sort(key=lambda x: int(x["id"]))
        print(f"✅ Fetched {len(issues)} issues")
        return {"issues": issues}
            
    except Exception as e:
        print(f"❌ Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

def process_issue(repo_url: str, issue_id: str, is_execution: bool = False):
    """Process a single issue (analysis or execution)."""
    try:
        print(f"🎯 Processing issue #{issue_id} ({'execution' if is_execution else 'analysis'})")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        if is_execution:
            # Execution flow - both agents use Devin API
            agent3 = PlanAgent()
            plan = safe_devin_api_call(agent3.review_files_and_plan, issue, repo_url)
            
            if not plan:
                return {"issue_id": issue_id, "error": "No plan available"}
            
            agent4 = ExecutorAgent()
            result = safe_devin_api_call(agent4.execute_and_push, plan, repo_url)
            
            return {
                "issue_id": issue_id,
                "status": "completed",
                "result": result,
                "pr_url": result.get("pr_url") if result else None
            }
        else:
            # Analysis flow - both agents use Devin API
            from utils.utils import get_cache_file_path, check_cache
            
            feasibility_cache = get_cache_file_path("cache", repo_url, "feasibility", issue_id)
            plan_cache = get_cache_file_path("cache", repo_url, "plan", issue_id)
            
            analysis = None
            plan = None
            
            # Get feasibility analysis
            if check_cache(feasibility_cache):
                print(f"✅ Using cached feasibility for issue #{issue_id}")
                with open(feasibility_cache, 'r') as f:
                    analysis = json.load(f)
            else:
                print(f"🔄 Running Agent 2 (feasibility) for issue #{issue_id}")
                agent2 = FeasibilityAnalyzerAgent()
                analysis = safe_devin_api_call(agent2.analyze_issue_feasibility, issue, repo_url)
            
            # Get plan
            if check_cache(plan_cache):
                print(f"✅ Using cached plan for issue #{issue_id}")
                with open(plan_cache, 'r') as f:
                    plan = json.load(f)
            else:
                print(f"🔄 Running Agent 3 (planning) for issue #{issue_id}")
                agent3 = PlanAgent()
                plan = safe_devin_api_call(agent3.review_files_and_plan, issue, repo_url)
            
            return {
                "issue_id": issue_id,
                "status": "completed",
                "analysis": analysis,
                "plan": plan
            }
            
    except Exception as e:
        print(f"❌ Processing failed for issue #{issue_id}: {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze a specific issue."""
    result = process_issue(request.repo_url, request.issue_id, is_execution=False)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/analyze-multiple-issues")
async def analyze_multiple_issues(request: MultiIssueRequest):
    """Analyze multiple issues with parallelization."""
    print(f"🔍 Analyzing {len(request.issue_ids)} issues")
    
    # Remove staggered delays - let the lock handle sequencing
    with ThreadPoolExecutor(max_workers=min(3, len(request.issue_ids))) as executor:
        results = list(executor.map(lambda issue_id: process_issue(request.repo_url, issue_id, is_execution=False), request.issue_ids))
    
    print(f"✅ Completed analysis of {len(results)} issues")
    return {"results": results}

@router.post("/api/execute")
async def execute_changes(request: IssueRequest):
    """Execute the plan and push changes."""
    result = process_issue(request.repo_url, request.issue_id, is_execution=True)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/execute-multiple-issues")
async def execute_multiple_issues(request: MultiIssueRequest):
    """Execute multiple issues with parallelization."""
    print(f"🚀 Executing {len(request.issue_ids)} issues")
    
    # Remove staggered delays - let the lock handle sequencing  
    with ThreadPoolExecutor(max_workers=min(2, len(request.issue_ids))) as executor:
        results = list(executor.map(lambda issue_id: process_issue(request.repo_url, issue_id, is_execution=True), request.issue_ids))
    
    print(f"✅ Completed execution of {len(results)} issues")
    return {"results": results}