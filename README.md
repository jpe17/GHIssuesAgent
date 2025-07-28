# GitHub Issues Analyzer

A modern, AI-powered GitHub issues analyzer that helps developers understand and resolve issues efficiently. Built with FastAPI, powered by Cognition AI and Devin AI.

## 🚀 Features

- **Three-Agent Workflow**: Intelligent workflow with specialized agents for different tasks
- **Real GitHub Integration**: Fetch actual issues from any public GitHub repository
- **AI-Powered Analysis**: Deep analysis of issues using Devin AI with repository context
- **Smart Caching**: Intelligent caching system for repository issues to improve performance
- **Human-in-the-Loop**: User input and approval at key decision points
- **Modern UI**: Beautiful dark theme with Cognition AI branding
- **Comprehensive Insights**: Scope assessment, technical analysis, effort estimation, and action plans

## 🤖 Three-Agent Architecture

### Agent 1: Issue Fetcher
- **Purpose**: Fetches GitHub issues and stores them in cache
- **Input**: Repository URL
- **Output**: Cached list of issues
- **Features**: Smart caching, error handling, repository validation

### Agent 2: Feasibility Analyzer
- **Purpose**: Calculates feasibility and complexity scores for issues
- **Input**: GitHub issue + repository context
- **Output**: Feasibility analysis with scores and technical assessment
- **Features**: Confidence scoring, effort estimation, risk assessment

### Agent 3: File Reviewer & Executor
- **Purpose**: Reviews files, creates action plan, and executes changes
- **Input**: Issue + feasibility analysis + user input
- **Output**: File changes and new branch with commits
- **Features**: File analysis, action planning, code execution, branch creation

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Devin AI API
- **GitHub Integration**: GitHub API via Devin AI
- **Caching**: File-based caching system
- **Styling**: Modern CSS with dark theme

## 📋 Prerequisites

- Python 3.8+
- Devin AI API key
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GHIssuesAgent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Devin AI API key**
   ```bash
   # Create a .env file
   echo "DEVIN_API_KEY=your_api_key_here" > .env
   ```
   
   Get your API key from [app.devin.ai](https://app.devin.ai)

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open your browser**
   Navigate to [http://localhost:8844](http://localhost:8844)

## 🎯 How to Use

### Option 1: Full Workflow (All Three Agents)
```bash
python run_workflow.py "https://github.com/owner/repo" "additional context"
```

### Option 2: Agents 2 & 3 Only
```bash
python run_agents_2_3.py "https://github.com/owner/repo"
```

### Option 3: Web Interface
1. Start the web server: `python main.py`
2. Open http://localhost:8844
3. Enter repository URL and follow the interface

## 🔄 Workflow Process

### Full Workflow (Agent 1 → Agent 2 → Human Input → Agent 3)

1. **Agent 1**: Fetches and caches GitHub issues
2. **Agent 2**: Analyzes feasibility of all issues
3. **Human Input**: User selects issue to work on
4. **Agent 3**: Reviews files and creates action plan
5. **Human Input**: User approves execution
6. **Agent 3**: Executes changes and creates new branch

### Agents 2 & 3 Workflow

1. **Manual Input**: User provides issue details
2. **Agent 2**: Analyzes feasibility and complexity
3. **Human Input**: User decides to proceed
4. **Agent 3**: Reviews files and creates action plan
5. **Human Input**: User approves execution
6. **Agent 3**: Executes changes and creates new branch

## 🏗️ Project Structure

```
GHIssuesAgent/
├── api/                           # AI and GitHub integration
│   ├── agent1_issue_fetcher.py   # Agent 1: Issue fetching
│   ├── agent2_feasibility_analyzer.py # Agent 2: Feasibility analysis
│   ├── agent3_plan.py            # Agent 3: Implementation planning
│   ├── agent4_executor.py        # Agent 4: Plan execution & GitHub push
│   ├── workflow_coordinator.py   # Workflow management
│   ├── config.py                 # Configuration and environment variables
│   ├── issues_service.py         # Legacy GitHub issues fetching service
│   ├── issue_analyzer.py         # Legacy AI-powered issue analysis
│   ├── repository_scanner.py     # Legacy repository scanning
│   └── session_manager.py        # Devin AI session management
├── app/                          # Web application
│   ├── static/                   # Static assets (CSS, images)
│   ├── templates/                # HTML templates
│   └── routes.py                 # FastAPI routes
├── cache/                        # Cached repository data
├── data/                         # Data files
├── main.py                       # Application entry point
├── run_workflow.py               # Full workflow runner
├── run_agents_2_3.py            # Agents 2 & 3 runner
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## 🎨 Design Features

- **Dark Theme**: Modern dark interface for better developer experience
- **Cognition AI Branding**: Professional branding with Cognition AI logo
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive Elements**: Hover effects, smooth transitions, and loading states
- **Status Indicators**: Real-time status updates for AI availability and cache status

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Devin AI API key
DEVIN_API_KEY=your_devin_api_key_here

# Optional: Custom API base URL
DEVIN_API_BASE=https://api.devin.ai/v1
```

### Cache Configuration

The application caches repository issues, feasibility analyses, and file reviews. Cache files are stored in the `cache/` directory with the following structure:

- `issues_{repo}.json` - Cached issues
- `feasibility_{repo}_{issue}.json` - Cached feasibility analyses
- `file_review_{repo}_{issue}.json` - Cached file reviews
- `execution_{repo}_{issue}.json` - Cached execution results

## 🚀 Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t github-issues-analyzer .
   ```

2. **Run the container**
   ```bash
   docker run -p 8844:8844 --env-file .env github-issues-analyzer
   ```

### Production Deployment

1. **Set up a production server**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment variables**
4. **Run with a production WSGI server**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8844
   ```

## 🔍 API Endpoints

- `GET /` - Main application interface
- `POST /fetch-issues` - Fetch and cache repository issues
- `POST /analyze-issue` - Analyze a specific issue with AI
- `GET /cache-info` - Get cache statistics
- `POST /clear-cache` - Clear all cached data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Cognition AI** for the AI-powered analysis capabilities
- **Devin AI** for the intelligent code analysis and repository scanning
- **FastAPI** for the modern Python web framework
- **GitHub** for the repository data and API

## 🆘 Support

If you encounter any issues:

1. Check that your `DEVIN_API_KEY` is properly set
2. Ensure the GitHub repository URL is valid and accessible
3. Check the application logs for detailed error messages
4. Open an issue on GitHub with detailed information

---

**Built with ❤️ by the GitHub Issues Analyzer team** 