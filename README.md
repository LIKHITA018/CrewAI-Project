CrewAI 10 Projects – FastAPI
A single-file FastAPI application that exposes ten original CrewAI projects as HTTP endpoints. The original project source files from the supplied ZIP are embedded in app.py and executed in isolated namespaces to avoid collisions between similarly named helpers.
Projects and endpoints
Endpoint	Project	Request JSON fields
POST /agent1	Blog Post Crew	topic
POST /agent2	Competitor Analysis Crew	competitors (array of strings)
POST /agent3	Meeting Notes Crew	transcript
POST /agent4	Data Report Crew	No request body
POST /agent5	Customer Support Flow	ticket_id, customer_name, issue_description
POST /agent6	Resume Screening Flow	job_title, job_description, resume_name, resume_text
POST /agent7	Bug Triage Flow	issue_title, issue_body
POST /agent8	Content Repurposing Flow	article_input
POST /agent9	Lead Qualification Flow	lead_name, lead_company, lead_website
POST /agent10	Approval Report Flow	topic, audience
POST /agent10/review	Human review for Approval Report Flow	flow_id, feedback


Successful project responses use the shape {"output": ...}. Errors are returned as FastAPI HTTP errors with a detail field.
Requirements
- Python 3.10 or newer (Python 3.11 is a sensible choice for deployment).
- A Gemini API key.
Local setup (Windows PowerShell)
1. Open PowerShell in the folder containing app.py.
2. Create and activate a virtual environment:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
3. Install dependencies:
   python -m pip install --upgrade pip
   pip install -r requirements.txt
4. Create a .env file in the same folder as app.py:
   GEMINI_API_KEY=your_gemini_api_key_here
   Do not upload or commit .env to GitHub.
5. Start the API:
   python -m uvicorn app:app --reload
6. Open the interactive API documentation at http://127.0.0.1:8000/docs.
Example requests
Agent 1 – Blog Post
{
  "topic": "How AI is changing education"
}
Agent 6 – Resume Screening
{
  "job_title": "Python Developer",
  "job_description": "Looking for Python, FastAPI, SQL and problem-solving skills.",
  "resume_name": "candidate_01",
  "resume_text": "Python developer with experience in FastAPI, SQL and Git."
}
Agent 7 – Bug Triage
{
  "issue_title": "Login button not responding",
  "issue_body": "The login button does nothing after valid credentials are entered."
}
Agent 10 – Approval Report
{
  "topic": "Responsible use of generative AI",
  "audience": "College students"
}
The Agent 10 flow may pause for human review and return a flow_id. Submit that ID and your feedback to POST /agent10/review.
Deployment (Render)
- Runtime: Python.
- Build command: pip install -r requirements.txt
- Start command: uvicorn app:app --host 0.0.0.0 --port $PORT
- Add GEMINI_API_KEY as a secret environment variable in the Render dashboard.
- Keep the Render root directory set to the directory containing app.py and requirements.txt.
Repository hygiene
Commit only the application and project documentation files. Do not commit .env, virtual environments, __pycache__, generated reports, or API keys.