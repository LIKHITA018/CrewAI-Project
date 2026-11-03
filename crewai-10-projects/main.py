import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form

# Load environment variables BEFORE importing projects
load_dotenv(override=True)

# Import CrewAI project functions
from projects.blog_post import run_blog_post
from projects.competitor_analysis import run_competitor_analysis
from projects.meeting_notes import run_meeting_notes
from projects.data_report import run_data_report
from projects.customer_support import run_customer_support
from projects.resume_screening import run_resume_screening_text
from projects.bug_triage import run_bug_triage
from projects.content_repurposing import run_content_repurposing
from projects.lead_qualification import run_lead_qualification


# Create FastAPI application
app.openapi_version = "3.0.3"



app = FastAPI(
    title="CrewAI 10 Projects API",
    docs_url="/docs"
)


# Home route
@app.get("/")
def home():
    return {
        "message": "CrewAI API is running!",
        "projects": 10
    }


# PROJECT 1: Blog Post Crew
@app.post("/agent1")
def agent1(data: dict):

    topic = data.get("input")

    if not topic:
        return {"error": "Please provide a blog topic."}

    try:
        result = run_blog_post(topic)

        return {
            "project": "Blog Post Crew",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}


# PROJECT 2: Competitor Analysis Crew
@app.post("/agent2")
def agent2(data: dict):

    competitors = data.get("input")

    if isinstance(competitors, str):
        competitors = competitors.split(",")

    if not isinstance(competitors, list) or len(competitors) != 3:
        return {
            "error": "Please provide exactly 3 competitor URLs."
        }

    try:
        result = run_competitor_analysis(competitors)

        return {
            "project": "Competitor Analysis Crew",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}




# PROJECT 3: Meeting Notes Crew
@app.post("/agent3")
def agent3(data: dict):

    transcript = data.get("input")

    if not transcript:
        return {"error": "Please provide a meeting transcript."}

    try:
        result = run_meeting_notes(transcript)

        return {
            "project": "Meeting Notes Crew",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}

    

@app.post("/agent4")
def agent4():
    try:
        result = run_data_report()

        return {
            "project": "Data Report Crew",
            "output": result
        }

    except Exception as e:
        return {
            "error": str(e)
        }

@app.post("/agent5")
def agent5(data: dict):
    try:
        result = run_customer_support(
            ticket_id=data.get("ticket_id", "TICKET-101"),
            customer_name=data.get("customer_name", "Rahul"),
            issue_description=data.get(
                "issue_description",
                "I was charged twice for my monthly subscription."
            )
        )

        return {
            "project": "Customer Support Flow",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}    

# PROJECT 6: Resume Screening Flow

@app.post("/agent6")
def agent6(data: dict):

    try:
        result = run_resume_screening_text(
            job_title=data.get("job_title", ""),
            job_description=data.get("job_description", ""),
            resume_name=data.get("resume_name", "Candidate Resume"),
            resume_text=data.get("resume_text", "")
        )

        return {
            "project": "Resume Screening Flow",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/agent7")
def agent7(data: dict):
    try:
        result = run_bug_triage(
            issue_title=data.get("issue_title", ""),
            issue_body=data.get("issue_body", "")
        )

        return {
            "project": "Bug Triage Flow",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}    

@app.post("/agent8")
def agent8(data: dict):
    try:
        result = run_content_repurposing(
            article_input=data.get("article_input", "")
        )

        return {
            "project": "Content Repurposing Flow",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}    

@app.post("/agent9")
def agent9(data: dict):
    try:
        result = run_lead_qualification(
            lead_name=data.get("lead_name", ""),
            lead_company=data.get("lead_company", ""),
            lead_website=data.get("lead_website", "")
        )

        return {
            "project": "Lead Qualification Flow",
            "output": result
        }

    except Exception as e:
        return {"error": str(e)}   

from pydantic import BaseModel
from projects.approval_report import (
    run_approval_report,
    review_approval_report
)

# PROJECT 10: Approval Report Flow

class ApprovalReportRequest(BaseModel):
    topic: str
    audience: str = "General audience"


class ApprovalReviewRequest(BaseModel):
    flow_id: str
    feedback: str


@app.post("/agent10")
def agent10(data: ApprovalReportRequest):
    try:
        result = run_approval_report(
            topic=data.topic,
            audience=data.audience
        )
        return {
            "project": "Approval Report Flow",
            "output": result
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/agent10/review")
def agent10_review(data: ApprovalReviewRequest):
    try:
        result = review_approval_report(
            flow_id=data.flow_id,
            feedback=data.feedback
        )
        return {
            "project": "Approval Report Flow",
            "output": result
        }
    except Exception as e:
        return {"error": str(e)}