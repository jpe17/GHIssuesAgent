# GitHub Issues Analyzer

A web application that analyzes GitHub issues using Devin AI to provide scope assessment, confidence scores, and technical analysis.

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
GHIssuesAgent/
├── api/                    # Core business logic (independent of web framework)
│   ├── __init__.py
│   ├── config.py           # Environment variables & timeouts
│   ├── session_manager.py  # Devin session handling
│   ├── issues_service.py   # GitHub issues fetching
│   ├── repository_scanner.py # File relevance scanning
│   └── issue_analyzer.py   # Two-phase issue analysis
├── app/                    # Web application layer
│   ├── static/             # CSS, JS, images
│   ├── templates/          # HTML templates
│   └── routes.py           # FastAPI routes
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_config.py      # Configuration tests
│   └── test_api_functions.py # Real API integration tests
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── Dockerfile             # Container configuration
```

## 🚀 Features

- **Two-Phase Analysis**: Smart repository scanning followed by targeted deep analysis
- **Session-Based API**: Robust Devin API integration with proper session management
- **Modular Design**: Clean separation of concerns for maintainability
- **Real API Testing**: Direct integration tests with actual Devin API
- **Web Interface**: User-friendly FastAPI web application

## 🛠️ Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd GHIssuesAgent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   DEVIN_API_KEY=your_devin_api_key_here
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Access the web interface**:
   Open your browser and go to `http://localhost:8000`

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Individual Test Files
Each test file can be run independently:

```bash
# Test configuration
pytest tests/test_config.py -v

# Test API functions with real Devin API
pytest tests/test_api_functions.py -v -s
```

### Test Coverage
The test suite includes:
- **Configuration Tests**: Environment variables and API key validation
- **Real API Integration Tests**: Direct calls to Devin API with actual responses
- **Workflow Tests**: Complete end-to-end testing of the application flow

### Testing Philosophy
- **Real API Calls**: Tests use actual Devin API to validate functionality
- **Basic Validation**: Focus on structure and basic functionality rather than exact content
- **Simple & Direct**: Each test file is self-contained and runnable independently

## 📋 API Components

### Core API Modules

#### `api/config.py`
- Environment variable management
- API endpoint configuration
- Timeout settings

#### `api/session_manager.py`
- Devin session creation and management
- Polling with exponential backoff
- Timeout handling

#### `api/issues_service.py`
- GitHub issues fetching
- Issue data formatting
- Single responsibility: just get issues

#### `api/repository_scanner.py`
- Phase 1: Quick repository scan
- Relevance scoring and file filtering
- Top files selection (max 10)

#### `api/issue_analyzer.py`
- Two-phase analysis orchestration
- Targeted vs full analysis
- Analysis result formatting

### Web Application

#### `app/routes.py`
- FastAPI route definitions
- Template rendering
- Form handling

#### `main.py`
- FastAPI application setup
- Session dependency injection
- Static file serving

## 🔄 Two-Phase Analysis

### Phase 1: Smart Scanning
- Quick scan of repository files
- Relevance scoring (1-10)
- Identifies top 10 most relevant files
- 3-minute timeout

### Phase 2: Deep Analysis
- **Targeted**: Analysis of identified relevant files (5-minute timeout)
- **Fallback**: Full repository analysis if scan fails (10-minute timeout)

## 🎯 Use Cases

1. **Repository Analysis**: Input a GitHub repository URL to fetch all open issues
2. **Issue Analysis**: Click "play" on any issue to get comprehensive analysis
3. **Scope Assessment**: Get size, complexity, and impact analysis
4. **Technical Insights**: Detailed technical analysis with file modifications
5. **Effort Estimation**: Time estimates and testing requirements

## 🔧 Development

### Adding New Features
1. Create a new service in the `api/` directory
2. Add corresponding tests in `tests/`
3. Update routes if needed
4. Run tests to ensure everything works

### Code Organization
- **Business Logic**: All in `api/` directory
- **Web Interface**: All in `app/` directory
- **Tests**: Real API integration tests in `tests/` directory
- **Configuration**: Centralized in `api/config.py`

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEVIN_API_KEY` | Your Devin AI API key | Yes |

## 🤝 Contributing

1. Follow the modular architecture
2. Add tests for new features using real API calls
3. Ensure all tests pass
4. Update documentation as needed

## 📄 License

This project is licensed under the MIT License. 