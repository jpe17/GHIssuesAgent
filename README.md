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
├── tests/                  # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest configuration & fixtures
│   ├── test_config.py      # Configuration tests
│   ├── test_session_manager.py # Session management tests
│   ├── test_issues_service.py # Issues service tests
│   ├── test_repository_scanner.py # Repository scanner tests
│   ├── test_issue_analyzer.py # Issue analyzer tests
│   ├── test_integration.py # Integration tests
│   └── run_tests.py        # Test runner script
├── main.py                 # FastAPI application entry point
├── test_devin.py          # Quick integration test script
└── requirements.txt       # Python dependencies
```

## 🚀 Features

- **Two-Phase Analysis**: Smart repository scanning followed by targeted deep analysis
- **Session-Based API**: Robust Devin API integration with proper session management
- **Modular Design**: Clean separation of concerns for maintainability
- **Comprehensive Testing**: Full test coverage for all components
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
python tests/run_tests.py
```

### Run Specific Test File
```bash
python tests/run_tests.py test_issues_service.py
```

### Run Tests with Pytest Directly
```bash
pytest tests/ -v
```

### Test Coverage
The test suite includes:
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Error Handling**: Edge cases and failure scenarios
- **Mock Testing**: Isolated testing without external dependencies

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
- **Tests**: Comprehensive coverage in `tests/` directory
- **Configuration**: Centralized in `api/config.py`

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEVIN_API_KEY` | Your Devin AI API key | Yes |

## 🤝 Contributing

1. Follow the modular architecture
2. Add tests for new features
3. Ensure all tests pass
4. Update documentation as needed

## 📄 License

This project is licensed under the MIT License. 