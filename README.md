# WorkSphere AI – 10 CrewAI Agents Platform

WorkSphere AI is a full-stack AI-powered platform that brings together ten intelligent CrewAI projects through a FastAPI backend and a modern React dashboard.

The application allows users to execute AI agents, generate intelligent outputs, track task history, monitor agent performance, and manage their workspace through a centralized interface.

## Project Overview

WorkSphere AI combines:

- **Frontend:** React.js and Vite
- **Backend:** Python and FastAPI
- **AI Framework:** CrewAI
- **LLM Provider:** Google Gemini
- **Deployment:** Render
- **Version Control:** Git and GitHub

## Key Features

### AI Agent Platform

The application includes ten specialized AI agents:

| Agent | Project | Function |
|---|---|---|
| Agent 1 | Blog Post Generator | Generates blog content |
| Agent 2 | Competitor Analysis | Analyzes competitors |
| Agent 3 | Meeting Notes | Processes meeting transcripts |
| Agent 4 | Data Report | Generates reports from sales data |
| Agent 5 | Customer Support | Handles customer support requests |
| Agent 6 | Resume Screening | Evaluates candidate resumes |
| Agent 7 | Bug Triage | Analyzes and categorizes bugs |
| Agent 8 | Content Repurposing | Repurposes existing content |
| Agent 9 | Lead Qualification | Evaluates potential leads |
| Agent 10 | Approval Report | Generates reports with human review |

### Dashboard Features

- Centralized AI agent dashboard
- Individual agent execution interface
- Input and output management
- Task history and search
- Agent performance monitoring
- Backend health monitoring
- Output copying and downloading
- Settings and workspace administration
- Responsive user interface

## Technology Stack

**Frontend**
- React.js
- Vite
- JavaScript
- CSS
- Lucide React Icons

**Backend**
- Python
- FastAPI
- CrewAI
- Pydantic
- Pandas

**AI Integration**
- Google Gemini API

**Deployment and Tools**
- Render
- GitHub
- Uvicorn
- REST API

## Project Structure

```text
CrewAI-Project/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── reports/
│   └── sales.csv
│
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── index.html
    ├── vite.config.js
    │
    ├── public/
    │
    └── src/
        ├── App.jsx
        ├── App.css
        ├── index.css
        ├── main.jsx
        └── assets/
```

## Backend API Endpoints

The FastAPI backend exposes ten AI agent endpoints and a human-review endpoint.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/agent1` | Blog Post Generator |
| POST | `/agent2` | Competitor Analysis |
| POST | `/agent3` | Meeting Notes |
| POST | `/agent4` | Data Report |
| POST | `/agent5` | Customer Support |
| POST | `/agent6` | Resume Screening |
| POST | `/agent7` | Bug Triage |
| POST | `/agent8` | Content Repurposing |
| POST | `/agent9` | Lead Qualification |
| POST | `/agent10` | Approval Report |
| POST | `/agent10/review` | Human Review |

Successful agent responses use an output field. Refer to the interactive Swagger documentation for the exact request schemas and response details.

## Local Installation and Setup

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- Google Gemini API key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/LIKHITA018/CrewAI-Project.git
cd CrewAI-Project
```

### 2. Set up the backend

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Never upload your API key or `.env` file to GitHub.

### 4. Start the backend

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Backend documentation:

```text
http://127.0.0.1:8000/docs
```

Backend health endpoint:

```text
http://127.0.0.1:8000/health
```

### 5. Set up the frontend

Open another terminal:

```bash
cd frontend
npm install
```

### 6. Start the frontend

```bash
npm run dev
```

Open the local Vite URL displayed in your terminal, usually:

```text
http://localhost:5173
```

The Vite development proxy forwards `/api` requests to the FastAPI backend.

## Production Deployment

### Backend – Render

The FastAPI backend is deployed on Render.

**Backend URL:**

https://agentiai-project-using-crewai.onrender.com

**API Documentation:**

https://agentiai-project-using-crewai.onrender.com/docs

**Health Monitoring:**

https://agentiai-project-using-crewai.onrender.com/health

Render configuration:

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Environment Variable: `GEMINI_API_KEY`

### Frontend – Render Static Site

The React frontend can be deployed as a Render Static Site.

Configuration:

- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`

Set the following environment variable:

```env
VITE_API_BASE_URL=https://agentiai-project-using-crewai.onrender.com
```

The frontend uses this URL to communicate directly with the deployed FastAPI backend.

The backend must allow requests from the deployed frontend origin through its CORS configuration.

## API Response and Error Handling

- Successful agent executions return generated output.
- Failed requests return FastAPI HTTP errors with a detail field.
- Backend health information provides agent execution statistics.
- Agent 10 supports a human-review workflow.

## Repository Hygiene

The repository excludes:

- `.env` files and API credentials
- Python virtual environments
- `node_modules`
- Python cache files
- Generated temporary files and reports

The required `reports/sales.csv` dataset is included for the Data Report agent.

## GitHub Repository

https://github.com/LIKHITA018/CrewAI-Project

## Project Goal

WorkSphere AI demonstrates how multiple specialized AI agents can be integrated into a single full-stack application using CrewAI, FastAPI, and React.

It provides a centralized environment for AI task execution, monitoring, and workflow management.
