"""Real API integration tests for GitHub Issues Analyzer."""

import pytest
import asyncio
import aiohttp
from api.issues_service import get_github_issues
from api.issue_analyzer import analyze_issue_with_devin_context
from api.repository_scanner import scan_repository_for_relevant_files
from api.config import DEVIN_API_KEY


class TestRealAPI:
    """Test actual Devin API integration."""
    
    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """Test that we can connect to the Devin API."""
        print(f"🔑 Testing with API key: {DEVIN_API_KEY[:10]}...")
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
        ) as session:
            # Test with a small, public repository
            repo_url = "https://github.com/octocat/Hello-World"
            
            try:
                print(f"📋 Fetching issues from: {repo_url}")
                issues = await get_github_issues(session, repo_url)
                
                print(f"✅ Successfully fetched {len(issues)} issues")
                if issues:
                    print(f"📝 First issue: #{issues[0].get('number')} - {issues[0].get('title')}")
                
                assert isinstance(issues, list)
                return True
                
            except Exception as e:
                print(f"❌ API Error: {str(e)}")
                pytest.fail(f"API connection failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_real_issue_analysis(self):
        """Test real issue analysis with a simple repository."""
        print("🔍 Testing real issue analysis...")
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
        ) as session:
            repo_url = "https://github.com/octocat/Hello-World"
            
            try:
                # First get issues
                issues = await get_github_issues(session, repo_url)
                
                if not issues:
                    print("⚠️ No issues found, skipping analysis test")
                    return
                
                # Test analysis on first issue
                issue = issues[0]
                issue_content = f"{issue.get('title')} - {issue.get('body', '')}"
                
                print(f"🔬 Analyzing issue #{issue.get('number')}: {issue.get('title')}")
                
                analysis = await analyze_issue_with_devin_context(
                    session,
                    issue_content,
                    repo_url,
                    issue.get('number')
                )
                
                print(f"✅ Analysis complete!")
                print(f"   Confidence: {analysis.get('score')}")
                print(f"   Method: {analysis.get('analysis_method')}")
                print(f"   Files analyzed: {analysis.get('files_analyzed')}")
                
                assert analysis is not None
                assert "score" in analysis
                assert "analysis_method" in analysis
                
                return True
                
            except Exception as e:
                print(f"❌ Analysis Error: {str(e)}")
                pytest.fail(f"Analysis failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_real_repository_scanning(self):
        """Test real repository scanning."""
        print("🔍 Testing real repository scanning...")
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
        ) as session:
            repo_url = "https://github.com/octocat/Hello-World"
            issue_content = "Fix a bug in the code"
            
            try:
                print(f"📁 Scanning repository: {repo_url}")
                relevant_files = await scan_repository_for_relevant_files(
                    session,
                    repo_url,
                    issue_content
                )
                
                print(f"✅ Scan complete! Found {len(relevant_files)} relevant files")
                if relevant_files:
                    print(f"📄 Top files: {relevant_files[:3]}")
                
                assert isinstance(relevant_files, list)
                return True
                
            except Exception as e:
                print(f"❌ Scan Error: {str(e)}")
                pytest.fail(f"Scanning failed: {str(e)}")


if __name__ == "__main__":
    # Run this test file directly
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements 