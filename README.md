# CrewAI – 10 AI Agent Projects with FastAPI

A collection of 10 AI-powered automation projects built using CrewAI, Google Gemini, Python, and FastAPI.

This project demonstrates how AI agents and agentic workflows can automate real-world tasks through REST API endpoints.

##  Project Overview

The application provides 10 different AI-powered projects, each designed to perform a specific task using AI agents or workflows.

##  Projects Included

| No. | Project Name | Description |
|---|---|---|
| 01 | Blog Post Crew | Generates engaging blog posts on given topics. |
| 02 | Competitor Analysis Crew | Analyzes competitors and generates reports. |
| 03 | Meeting Notes Crew | Converts meeting transcripts into structured notes. |
| 04 | Data Report Crew | Analyzes data and generates reports. |
| 05 | Customer Support Flow | Processes customer queries and support tickets. |
| 06 | Resume Screening Flow | Evaluates resumes against job requirements. |
| 07 | Bug Triage Flow | Analyzes software bugs and categorizes issues. |
| 08 | Content Repurposing Flow | Converts content into multiple formats. |
| 09 | Lead Qualification Flow | Evaluates and qualifies potential leads. |
| 10 | Approval Report Flow | Generates reports with a human approval process. |

##  Technologies Used

- Python
- CrewAI
- FastAPI
- Google Gemini API
- DuckDuckGo Search
- Pydantic
- Uvicorn
- Python-dotenv

##  Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/LIKHITA018/CrewAI-Project.git
cd CrewAI-Project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Gemini API key

Create a `.env` file and add:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Use the environment variable name expected by your application.

### 6. Run the FastAPI application

```bash
uvicorn main:app --reload
```

##  API Endpoints

| Method | Endpoint | Function |
|---|---|---|
| GET | `/` | API homepage |
| POST | `/agent1` | Blog Post Crew |
| POST | `/agent2` | Competitor Analysis |
| POST | `/agent3` | Meeting Notes |
| POST | `/agent4` | Data Report |
| POST | `/agent5` | Customer Support |
| POST | `/agent6` | Resume Screening |
| POST | `/agent7` | Bug Triage |
| POST | `/agent8` | Content Repurposing |
| POST | `/agent9` | Lead Qualification |
| POST | `/agent10` | Approval Report |
| POST | `/agent10/review` | Human Approval |

## 📖API Documentation

FastAPI provides interactive API documentation through Swagger UI.

After starting the application, visit:

```text
http://127.0.0.1:8000/docs
```

##  Deployment

The application is deployed using Render.

**Live Application:**  
https://crewai-project.onrender.com

**API Documentation:**  
https://crewai-project.onrender.com/docs

##  Learning Outcomes

- Understanding AI agents and agentic workflows.
- Building multi-agent systems using CrewAI.
- Integrating Google Gemini with Python applications.
- Developing REST APIs using FastAPI.
- Implementing human-in-the-loop approval workflows.
- Deploying AI applications using cloud hosting.

 Author

Likhita Chepuri

GitHub: [LIKHITA018](https://github.com/LIKHITA018)

---

*Built as part of an Agentic AI learning project, exploring the journey from AI prototypes to production-ready applications.*