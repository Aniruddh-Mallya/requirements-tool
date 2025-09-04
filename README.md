# ReqTool MVP

A comprehensive requirements analysis tool that processes user feedback and automatically generates Software Requirements Specifications (SRS) documents and user stories. The tool integrates with Jira for seamless project management workflow.

## 🚀 Features

### Core Functionality
- **User Feedback Classification**: Automatically categorizes user reviews into Bug Reports, Feature Requests, or Other
- **SRS Generation**: Converts classified feedback into comprehensive Software Requirements Specification documents
- **User Story Generation**: Transforms SRS requirements into user stories following the "As a... I want... so that..." format
- **Jira Integration**: Directly create Jira issues from classified feedback and generated user stories
- **Batch Processing**: Handle multiple reviews simultaneously with selective sending to Jira

### Technical Features
- **AI-Powered Analysis**: Uses Ollama/Mistral for intelligent feedback classification and requirement generation
- **Modern Web Interface**: React-based frontend with intuitive file upload and selection interface
- **RESTful API**: FastAPI backend with comprehensive endpoints for all operations
- **Real-time Processing**: Immediate feedback classification and SRS generation
- **Error Handling**: Robust error handling with detailed logging and user feedback

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **`main.py`**: Core API endpoints and request handling
- **`llm_client.py`**: AI integration using Ollama/Mistral for classification and SRS generation
- **`jira_client.py`**: Jira API integration for issue creation
- **`requirements.txt`**: Python dependencies

### Frontend (React/TypeScript)
- **`App.tsx`**: Main application component with file upload and results display
- **`api.ts`**: API client functions for backend communication
- **Modern UI**: Clean, responsive interface with real-time feedback

### Datasets
- **`BOW_test.txt`**: Sample user feedback data for testing
- **`NFR.xlsx`**: Non-functional requirements dataset

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama (with Mistral model)
- Jira instance (optional, for issue creation)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Jira Configuration (optional)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJECT
```

## 🚀 Running the Application

### Start the Backend
```bash
cd backend
uvicorn main:app --reload --port 8001
```

### Start the Frontend
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## 📖 Usage Guide

### 1. Upload User Feedback
- Click "Choose File" and select a `.txt` file containing user reviews
- Each line should contain one user review/feedback
- The system will automatically process and classify all reviews

### 2. Review Classifications
- View the automatic classification results (Bug, Feature, Other)
- See reasoning for each classification
- Use "Select All" or "Clear All" to manage selections
- Select specific items to send to Jira

### 3. Generate SRS Document
- After processing, a comprehensive SRS document is automatically generated
- The SRS includes:
  - Introduction and Purpose
  - System Overview
  - Functional Requirements
  - Non-Functional Requirements
  - System Features
  - External Interfaces
  - Performance Requirements
  - Design Constraints

### 4. Generate User Stories
- Click "Generate User Stories" to convert SRS requirements into user stories
- Stories follow the format: "As a <user>, I want <goal> so that <reason>"
- Select specific stories to send to Jira

### 5. Send to Jira
- Select classified feedback or user stories
- Click "Send Selected to Jira" to create issues
- Maximum 10 items can be sent at once
- Issues are created with appropriate labels and descriptions

## 🔧 API Endpoints

### Core Processing
- `POST /process` - Process uploaded text file and return classifications + SRS
- `POST /stories/generate` - Generate user stories from SRS document

### Jira Integration
- `POST /jira/send-selected-classifications` - Send selected classifications to Jira
- `POST /jira/send-selected` - Send selected user stories to Jira
- `GET /` - Health check and configuration status

## 🤖 AI Integration

The tool uses Ollama with the Mistral model for:
- **Feedback Classification**: Few-shot learning approach with predefined examples
- **SRS Generation**: Constraint-based prompting for structured requirement documents
- **User Story Generation**: Template-based conversion of requirements to user stories

### Classification Categories
- **Bug Report**: Errors, faults, or unintended behavior
- **Feature Request**: New functionality or enhancements
- **Other**: General feedback, compliments, or non-specific comments

## 📊 Sample Data

The tool includes sample datasets:
- **BOW_test.txt**: Contains 512 user reviews with classifications for testing
- **NFR.xlsx**: Non-functional requirements dataset for advanced analysis

## 🔒 Security & Best Practices

- CORS is configured for development (should be locked down for production)
- Environment variables for sensitive configuration
- Input validation and error handling
- Rate limiting on Jira API calls (max 10 items per request)

## 🚧 Development Notes

- The backend runs on port 8001
- Frontend development server runs on port 5173
- Hot reloading enabled for both frontend and backend
- Comprehensive error logging and user feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is part of a requirements analysis tool MVP. Please ensure proper licensing for production use.

## 🆘 Support

For issues or questions:
1. Check the error logs in the application
2. Verify Ollama is running with the Mistral model
3. Ensure Jira credentials are correctly configured
4. Check file format requirements (.txt files only)

---

**ReqTool MVP** - Transforming user feedback into actionable requirements
