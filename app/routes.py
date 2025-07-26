"""FastAPI routes for the GitHub Issues Analyzer web interface."""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from api.issues_service import get_github_issues
from api.issue_analyzer import analyze_issue_with_devin_context
import re
import aiohttp

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_devin_session() -> aiohttp.ClientSession:
    """Dependency to get the Devin session."""
    # This will be overridden in main.py
    return None

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/fetch-issues", response_class=HTMLResponse)
async def fetch_issues(
    request: Request, 
    repo_url: str = Form(...), 
    devin_session: aiohttp.ClientSession = Depends(get_devin_session)
):
    """Fetch GitHub issues for a repository."""
    try:
        # Extract owner and repo from GitHub URL for display
        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, repo_url)
        if not match:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Invalid GitHub repository URL",
                "repo_url": repo_url
            })
        
        owner, repo = match.groups()
        
        # Get issues using Devin sessions
        issues = await get_github_issues(devin_session, repo_url)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "issues": issues,
            "repo_url": repo_url,
            "owner": owner,
            "repo": repo
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error fetching repository data: {str(e)}",
            "repo_url": repo_url
        })

@router.post("/analyze-issue", response_class=HTMLResponse)
async def analyze_issue(
    request: Request, 
    issue_content: str = Form(...), 
    issue_number: int = Form(...), 
    repo_url: str = Form(None),
    devin_session: aiohttp.ClientSession = Depends(get_devin_session)
):
    """Analyze a specific GitHub issue."""
    try:
        # Use Devin for comprehensive issue analysis with full repository context
        analysis_result = await analyze_issue_with_devin_context(devin_session, issue_content, repo_url, issue_number)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "analysis_result": {
                "issue_number": issue_number,
                "score": analysis_result["score"],
                "action": analysis_result["action"],
                "scope": analysis_result["scope"],
                "technical_analysis": analysis_result["technical_analysis"],
                "effort_estimation": analysis_result["effort_estimation"],
                "related_considerations": analysis_result["related_considerations"],
                "analysis_method": analysis_result["analysis_method"],
                "files_analyzed": analysis_result["files_analyzed"]
            },
            "repo_url": repo_url
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error analyzing issue: {str(e)}",
            "repo_url": repo_url
        }) 