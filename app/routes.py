"""Simple FastAPI routes for GitHub Issues Agent frontend."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflows import fetch_repository_issues, process_issue_parallel, execute_issue_plan

router = APIRouter()

# Request models
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
        print(f"🔄 Fetching issues from: {request.repo_url}")
        issues = fetch_repository_issues(request.repo_url)
        print(f"✅ Fetched {len(issues)} issues")
        return {"issues": issues}
    except Exception as e:
        print(f"❌ Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze one issue (feasibility + planning in parallel)."""
    result = process_issue_parallel(request.repo_url, request.issue_id)
    if "error" in result:
        raise HTTPException(status_code=404 if "not found" in result["error"] else 500, detail=result["error"])
    return result

@router.post("/api/plan")
async def create_plan(request: IssueRequest):
    """Create execution plan for an issue."""
    result = process_issue_parallel(request.repo_url, request.issue_id)
    if "error" in result:
        raise HTTPException(status_code=404 if "not found" in result["error"] else 500, detail=result["error"])
    return {"plan": result["plan"]}

@router.post("/api/analyze-multiple-issues")
async def analyze_multiple_issues(request: MultiIssueRequest):
    """Analyze multiple issues (same as single issue, just repeated)."""
    with ThreadPoolExecutor(max_workers=min(3, len(request.issue_ids))) as executor:
        results = list(executor.map(
            lambda issue_id: process_issue_parallel(request.repo_url, issue_id), 
            request.issue_ids
        ))
    
    return {"results": results}

@router.post("/api/execute")
async def execute_plan(request: IssueRequest):
    """Execute the plan and create PR."""
    result = execute_issue_plan(request.repo_url, request.issue_id)
    if "error" in result:
        raise HTTPException(status_code=404 if "not found" in result["error"] else 500, detail=result["error"])
    return result