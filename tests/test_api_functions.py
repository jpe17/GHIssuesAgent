"""Simple tests for API functions using real Devin API."""

import pytest
import asyncio
import aiohttp
from api.issues_service import get_github_issues
from api.issue_analyzer import analyze_issue_with_devin_context
from api.repository_scanner import scan_repository_for_relevant_files
from api.config import DEVIN_API_KEY


@pytest.mark.asyncio
async def test_get_issues():
    """Test getting issues from a real repository."""
    print("🔍 Testing get_github_issues...")
    
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
    ) as session:
        # Test with a small public repo
        repo_url = "https://github.com/octocat/Hello-World"
        
        issues = await get_github_issues(session, repo_url)
        
        # Basic validation - it should return a list
        assert isinstance(issues, list)
        print(f"✅ Got {len(issues)} issues")
        
        # If there are issues, check basic structure
        if issues:
            issue = issues[0]
            assert "number" in issue
            assert "title" in issue
            assert "body" in issue
            print(f"📝 Sample issue: #{issue['number']} - {issue['title']}")
        
        return issues


@pytest.mark.asyncio
async def test_scan_repository():
    """Test repository scanning."""
    print("🔍 Testing scan_repository_for_relevant_files...")
    
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
    ) as session:
        repo_url = "https://github.com/octocat/Hello-World"
        issue_content = "Fix a bug in the code"
        
        relevant_files = await scan_repository_for_relevant_files(
            session, repo_url, issue_content
        )
        
        # Basic validation
        assert isinstance(relevant_files, list)
        print(f"✅ Found {len(relevant_files)} relevant files")
        
        if relevant_files:
            print(f"📄 Top files: {relevant_files[:3]}")
        
        return relevant_files


@pytest.mark.asyncio
async def test_analyze_issue():
    """Test issue analysis."""
    print("🔍 Testing analyze_issue_with_devin_context...")
    
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
    ) as session:
        repo_url = "https://github.com/octocat/Hello-World"
        
        # First get an issue to analyze
        issues = await get_github_issues(session, repo_url)
        
        if not issues:
            print("⚠️ No issues found, skipping analysis")
            return
        
        issue = issues[0]
        issue_content = f"{issue['title']} - {issue['body']}"
        
        print(f"🔬 Analyzing issue #{issue['number']}: {issue['title']}")
        
        analysis = await analyze_issue_with_devin_context(
            session, issue_content, repo_url, issue['number']
        )
        
        # Basic validation
        assert isinstance(analysis, dict)
        assert "score" in analysis
        assert "analysis_method" in analysis
        assert "files_analyzed" in analysis
        
        print(f"✅ Analysis complete!")
        print(f"   Confidence: {analysis['score']}")
        print(f"   Method: {analysis['analysis_method']}")
        print(f"   Files: {analysis['files_analyzed']}")
        
        return analysis


@pytest.mark.asyncio
async def test_full_workflow():
    """Test the complete workflow."""
    print("🚀 Testing complete workflow...")
    
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
    ) as session:
        repo_url = "https://github.com/octocat/Hello-World"
        
        # Step 1: Get issues
        issues = await get_github_issues(session, repo_url)
        print(f"📋 Step 1: Got {len(issues)} issues")
        
        if not issues:
            print("⚠️ No issues found, workflow complete")
            return
        
        # Step 2: Analyze first issue
        issue = issues[0]
        issue_content = f"{issue['title']} - {issue['body']}"
        
        analysis = await analyze_issue_with_devin_context(
            session, issue_content, repo_url, issue['number']
        )
        
        print(f"🔬 Step 2: Analysis complete")
        print(f"   Score: {analysis['score']}")
        print(f"   Method: {analysis['analysis_method']}")
        
        print("✅ Full workflow successful!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements 