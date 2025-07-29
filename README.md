# GitHub Issues Agent

AI-powered GitHub issues analyzer using Devin AI. Automates issue analysis, feasibility assessment, and implementation planning.

## Features

- **Four-Agent System**: Issue fetching, feasibility analysis, implementation planning, and execution
- **GitHub Integration**: Direct access to repository issues and code
- **AI Analysis**: Devin AI-powered issue assessment and technical analysis
- **Smart Caching**: Local caching for performance optimization
- **Web Interface**: FastAPI-based UI for issue management

## Architecture

### Agent 1: Issue Fetcher
- Fetches GitHub issues and caches them locally
- Input: Repository URL
- Output: Cached issue data

### Agent 2: Feasibility Analyzer  
- Analyzes issue complexity and feasibility
- Provides technical assessment and risk analysis
- Output: Feasibility scores and technical recommendations

### Agent 3: Implementation Planner
- Reviews repository files and creates action plans
- Generates step-by-step implementation strategies
- Output: Detailed execution plans

### Agent 4: Executor
- Executes approved implementation plans
- Creates new branches and commits changes
- Pushes to GitHub and creates pull requests
- Output: Pull request URL and execution status

## Setup

### Prerequisites
- Python 3.8+
- Devin AI API key
- Git

### Installation
```bash
git clone <repo>
cd GHIssuesAgent
pip install -r requirements.txt
```

### Configuration
Create `.env` file:
```env
DEVIN_API_KEY=your_devin_api_key_here
```

Get API key from [app.devin.ai](https://app.devin.ai)

### Run
```bash
python main.py
```
Access at http://localhost:8844

## Usage

### Web Interface
1. Start server: `python main.py`
2. Open http://localhost:8844
3. Enter repository URL
4. Select issues for analysis

### Command Line
```bash
# Full workflow (all 4 agents)
python scripts/run_agents.py "https://github.com/owner/repo"

# Agents 2 & 3 only
python run_agents_2_3.py "https://github.com/owner/repo"
```

## Project Structure
```
GHIssuesAgent/
├── agents/                       # Agent implementations
├── app/                         # Web application
├── core/                        # Core functionality
├── cache/                       # Cached data
├── utils/                       # Utilities
└── main.py                      # Entry point
```

## API Endpoints
- `GET /` - Main interface
- `POST /api/fetch-issues` - Fetch repository issues
- `POST /api/analyze-issue` - Analyze specific issue
- `POST /api/execute` - Execute implementation plan
- `POST /api/execute-multiple-issues` - Execute multiple issues in parallel

## Configuration

### Environment Variables
- `DEVIN_API_KEY` - Devin AI API key (required)
- `DEVIN_API_BASE` - API base URL (optional, defaults to https://api.devin.ai/v1)

### Cache
- Issues cached in `cache/issues/`
- Analysis results cached per issue
- Automatic cache management

## Deployment

### Production
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8844
```

### Docker
```bash
docker build -t github-issues-agent .
docker run -p 8844:8844 --env-file .env github-issues-agent
```

## Troubleshooting

1. Verify `DEVIN_API_KEY` is set correctly
2. Check repository URL is accessible
3. Review application logs for errors
4. Ensure sufficient API quota for Devin AI

## License

MIT License 