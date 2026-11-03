

import os
import re
import json
import pandas as pd

from pathlib import Path
from ddgs import DDGS
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.flow.flow import Flow, start, listen, router, or_


# ============================================================
# 1. ENVIRONMENT AND GEMINI API KEY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Please check your .env file."
    )

os.environ["GEMINI_API_KEY"] = api_key

llm = LLM(
    model="gemini/gemini-3.5-flash",
    api_key=os.environ["GEMINI_API_KEY"]
)

SHORTLIST_SCORE = 7


# ============================================================
# 2. DDGS JOB SKILLS SEARCH
# ============================================================

def search_job_skills(query):
    try:
        results = DDGS().text(query, max_results=5)

        return json.dumps(
            [
                {
                    "title": x.get("title", ""),
                    "description": x.get("body", ""),
                    "url": x.get("href", "")
                }
                for x in (results or [])
            ],
            ensure_ascii=False
        )

    except Exception as e:
        return f"DDGS search unavailable: {e}"


# ============================================================
# 3. PARSE GEMINI JSON
# ============================================================

def parse_json(response):

    text = str(response).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            text,
            re.S
        )

        if match:
            return json.loads(match.group())

        raise ValueError("Gemini did not return valid JSON.")


# ============================================================
# 4. FLOW STATE
# ============================================================

class ResumeState(BaseModel):

    resume_name: str = ""
    resume_text: str = ""

    job_title: str = ""
    job_description: str = ""

    score: int = 0
    summary: str = ""

    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)

    review_note: str = ""
    decision: str = ""
    email_draft: str = ""


# ============================================================
# 5. RESUME SCREENING FLOW
# ============================================================

class ResumeScreeningFlow(Flow[ResumeState]):

    @start()
    def load_resumes(self):

        print("\nLoading:", self.state.resume_name)

        return self.state.resume_name


    @listen(load_resumes)
    def score_resume(self, resume_name):

        print("Researching job skills using DDGS...")

        research = search_job_skills(
            f"{self.state.job_title} required skills job role"
        )

        prompt = f"""
Compare this resume against the job description.

JOB TITLE:
{self.state.job_title}

JOB DESCRIPTION:
{self.state.job_description}

RESUME:
{self.state.resume_text[:15000]}

PUBLIC JOB SKILLS RESEARCH:
{research[:4000]}

The job description is the main evaluation standard.
Web research is supplementary.

Return ONLY valid JSON:

{{
    "score": 0,
    "summary": "brief evidence-based summary",
    "strengths": ["relevant evidence"],
    "gaps": ["requirements not evidenced"],
    "review_note": "what a human should verify"
}}

Score must be an integer from 0 to 10.

Do not invent skills or qualifications.
Missing evidence does not prove lack of ability.
Do not score protected or personal characteristics.
The result is for human review only.
"""

        data = parse_json(llm.call(prompt))

        self.state.score = max(
            0,
            min(10, int(data.get("score", 0)))
        )

        self.state.summary = str(
            data.get("summary", "")
        )

        self.state.strengths = [
            str(x) for x in data.get("strengths", [])
        ]

        self.state.gaps = [
            str(x) for x in data.get("gaps", [])
        ]

        self.state.review_note = str(
            data.get("review_note", "")
        )

        print("Score:", self.state.score, "/ 10")

        return self.state.score


    @router(score_resume)
    def check_score(self, score):

        if score >= SHORTLIST_SCORE:
            return "shortlist"

        return "review"


    # --------------------------------------------------------
    # SHORTLIST BRANCH
    # --------------------------------------------------------

    @listen("shortlist")
    def shortlist_summary(self):

        agent = Agent(
            role="Resume Summary Specialist",

            goal="Summarize relevant resume strengths and gaps.",

            backstory=(
                "You prepare accurate, concise recruiter "
                "review summaries."
            ),

            llm=llm,
            verbose=False
        )

        task = Task(
            description=f"""
Prepare a concise summary for human review.

Job: {self.state.job_title}

Score: {self.state.score}/10

Analysis: {self.state.summary}

Strengths: {self.state.strengths}

Gaps: {self.state.gaps}

Do not invent facts or make a final hiring decision.
""",

            expected_output="Concise resume review summary.",

            agent=agent
        )

        result = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        ).kickoff()

        self.state.summary = str(result)

        self.state.decision = "Shortlist for human review"

        return self.state.decision


    # --------------------------------------------------------
    # FURTHER REVIEW BRANCH
    # --------------------------------------------------------

    @listen("review")
    def draft_rejection(self):

        agent = Agent(
            role="Recruitment Email Assistant",

            goal="Prepare a respectful recruitment email draft.",

            backstory=(
                "You write neutral and professional "
                "recruitment messages."
            ),

            llm=llm,
            verbose=False
        )

        task = Task(
            description=f"""
Draft a polite email for a recruiter to review.

Job: {self.state.job_title}

Do not claim the candidate is unsuitable based solely
on an automated score.

Do not invent facts.

Make clear this is only a draft for human review.
""",

            expected_output=(
                "Email subject and body for recruiter review."
            ),

            agent=agent
        )

        self.state.email_draft = str(
            Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            ).kickoff()
        )

        self.state.decision = "Further human review"

        self.state.review_note += (
            " Human review is required before any decision."
        )

        return self.state.decision


    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    @listen(or_(shortlist_summary, draft_rejection))
    def save_results(self):

        return {
            "Resume": self.state.resume_name,
            "Score": self.state.score,
            "Decision": self.state.decision,
            "Summary": self.state.summary,
            "Strengths": "; ".join(self.state.strengths),
            "Skill Gaps": "; ".join(self.state.gaps),
            "Review Notes": self.state.review_note,
            "Email Draft": self.state.email_draft
        }


# ============================================================
# 6. RUN RESUME SCREENING USING PASTED TEXT
# ============================================================

def run_resume_screening_text(
    job_title,
    job_description,
    resume_name,
    resume_text
):

    if not job_title.strip():
        raise ValueError("Please provide a job title.")

    if not job_description.strip():
        raise ValueError("Please provide a job description.")

    if not resume_text.strip():
        raise ValueError("Please provide resume text.")

    flow = ResumeScreeningFlow()

    flow.state.resume_name = resume_name
    flow.state.resume_text = resume_text
    flow.state.job_title = job_title
    flow.state.job_description = job_description

    output = flow.kickoff()

    if isinstance(output, dict):

        result = output

    else:

        result = {
            "Resume": flow.state.resume_name,
            "Score": flow.state.score,
            "Decision": flow.state.decision,
            "Summary": flow.state.summary,
            "Strengths": "; ".join(flow.state.strengths),
            "Skill Gaps": "; ".join(flow.state.gaps),
            "Review Notes": flow.state.review_note,
            "Email Draft": flow.state.email_draft
        }

    results_df = pd.DataFrame([result])

    csv_path = REPORTS_DIR / "results.csv"

    results_df.to_csv(
        csv_path,
        index=False
    )

    return {
        "total_resumes": 1,
        "results": result,
        "csv_file": str(csv_path)
    }
