# GitHub Issues Agent Frontend

A modern, clean web interface for the GitHub Issues Agent that provides the same functionality as the command-line `run_agents.py` script, but with a beautiful UI.

## Features

- 🎨 **Modern Dark Theme**: Clean, professional interface inspired by Devin AI and Cognition AI
- 🔍 **Repository Issue Fetching**: Fetch and display all issues from any GitHub repository
- 🤖 **AI-Powered Analysis**: Real-time feasibility analysis and implementation planning
- 🚀 **One-Click Execution**: Execute changes and create pull requests with a single click
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices
- ⚡ **Simple & Fast**: Direct API calls without complex session management

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file in the root directory:
   ```bash
   DEVIN_API_KEY=your_devin_api_key_here
   ```

3. **Run the Frontend**:
   ```bash
   python run_frontend.py
   ```

4. **Open in Browser**:
   Navigate to `http://localhost:8844`

## How to Use

### 1. Enter Repository URL
- Enter a GitHub repository URL (e.g., `https://github.com/username/repo`)
- Click "Fetch Issues" to load all issues from the repository

### 2. Select an Issue
- Browse through the fetched issues
- Click on any issue card to select it
- The selected issue will be highlighted

### 3. Analyze the Issue
- Click the "▶️ Analyze" button next to any issue to start AI analysis
- The system will run both feasibility analysis and implementation planning
- The issue row will show "Analyzing..." status during processing

### 4. Review Results
- **Feasibility Analysis**: See the feasibility score (0-100) and any identified risks
- **Implementation Plan**: Review the detailed action plan with step-by-step instructions

### 5. Execute Changes
- Click "Execute & Push Changes" to implement the solution
- The system will create a pull request with the changes
- View the PR link when execution completes

## UI Components

### Repository Input Section
- Clean input field for GitHub repository URLs
- Fetch button with loading states

### Issues List
- Linear layout with one issue per row
- Issue number, title, state, and description
- Play button for each issue to start analysis
- Visual feedback during analysis

### Analysis Results
- **Feasibility Score**: Visual circular progress indicator
- **Risk Assessment**: Clear warning indicators for potential issues
- **Implementation Plan**: Step-by-step action items with file references

### Execution Status
- Real-time progress updates
- Success/error states with clear messaging
- Direct links to created pull requests

## Technical Details

### Backend API Endpoints
- `POST /api/fetch-issues`: Fetch issues from a repository
- `POST /api/analyze-issue`: Run AI analysis of an issue (returns results directly)
- `POST /api/execute`: Execute the implementation plan (returns results directly)

### Frontend Technologies
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with gradients and animations
- **Vanilla JavaScript**: No framework dependencies
- **Responsive Design**: Mobile-first approach

### Simple Architecture
- Direct API calls without polling or background tasks
- Synchronous processing for immediate results
- No complex session management

## Troubleshooting

### Common Issues

1. **"Failed to fetch issues"**
   - Check if the repository URL is correct
   - Ensure the repository is public or you have access
   - Verify your internet connection

2. **"Analysis failed"**
   - Check your Devin API key is set correctly
   - Ensure the API key has sufficient credits
   - Try with a simpler issue first

3. **"Execution failed"**
   - Check if the repository allows pull requests
   - Ensure the Devin session completed successfully
   - Review the error message for specific details

### Environment Variables
Make sure these are set in your `.env` file:
```bash
DEVIN_API_KEY=your_devin_api_key_here
```

## Development

### Running in Development Mode
The frontend includes hot-reload for development:
```bash
python run_frontend.py
```

### File Structure
```
app/
├── static/
│   └── index.html          # Main frontend application
├── routes.py               # FastAPI routes and API endpoints
└── cognition.jpeg          # Assets
```

### Customization
- Modify `app/static/index.html` to change the UI
- Update `app/routes.py` to modify API behavior
- Adjust CSS variables in the HTML file for theming

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## License

This frontend is part of the GitHub Issues Agent project and follows the same license terms. 