
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai.flow.flow import Flow, start, listen, router, or_
from ddgs import DDGS


# 1. API KEY SETUP
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")


# 2. SCHEMAS
class BugAnalysis(BaseModel):
    severity: str = Field(
        description="Severity: Critical, High, Medium, or Low"
    )
    suspected_component: str = Field(
        description="Component likely affected"
    )
    reproduction_steps: List[str] = Field(
        description="Steps to reproduce"
    )
    immediate_action: str = Field(
        description="Next action"
    )


class FeatureStory(BaseModel):
    user_story: str = Field(description="User story")
    acceptance_criteria: List[str] = Field(
        description="Acceptance criteria"
    )


class DocAnswer(BaseModel):
    direct_answer: str = Field(description="Answer")
    sources: List[str] = Field(description="Sources")


class BugTriageState(BaseModel):
    issue_title: str = ""
    issue_body: str = ""
    classified_type: str = ""
    triage_output: str = ""
    final_reply: str = ""


# 3. SEARCH TOOL
@tool("DuckDuckGo Search")
def duckduckgo_search(query: str) -> str:
    """Search the web and technical documentation using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=3)

        output = [
            f"Title: {r['title']}\n"
            f"Link: {r['href']}\n"
            f"Summary: {r['body']}"
            for r in results
        ]

        return "\n\n".join(output) if output else "No results found."

    except Exception as e:
        return f"Search failed: {e}"


# 4. LLM
llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=api_key,
    temperature=0.2,
)


# 5. BUG TRIAGE FLOW
class BugTriageFlow(Flow[BugTriageState]):

    @start()
    def read_issue(self):
        print(f"\n[1/4] Reading Issue: '{self.state.issue_title}'")

        return {
            "title": self.state.issue_title,
            "body": self.state.issue_body
        }

    @listen(read_issue)
    def classify_issue(self):
        print("[2/4] Classifying issue with direct LLM call...")

        prompt = (
            "Classify this issue strictly as one word: "
            "'bug', 'feature', or 'question'.\n"
            f"Title: {self.state.issue_title}\n"
            f"Body: {self.state.issue_body}"
        )

        response = llm.call(
            messages=[{"role": "user", "content": prompt}]
        ).strip().lower()

        if "bug" in response:
            self.state.classified_type = "bug"
        elif "feature" in response:
            self.state.classified_type = "feature"
        else:
            self.state.classified_type = "question"

        print(
            f"Result: Classified as "
            f"'{self.state.classified_type}'"
        )

        return self.state.classified_type

    @router(classify_issue)
    def route_type(self):
        return self.state.classified_type

    @listen("bug")
    def run_bug_crew(self):
        print("[3/4] Running Bug Crew...")

        agent = Agent(
            role="QA Engineer",
            goal="Identify root causes and reproduction steps",
            backstory="Senior QA engineer triaging incoming bugs.",
            llm=llm,
            verbose=True,
        )

        task = Task(
            description=(
                f"Analyze bug report:\n"
                f"Title: {self.state.issue_title}\n"
                f"Body: {self.state.issue_body}"
            ),
            expected_output="Structured severity and steps.",
            agent=agent,
            output_pydantic=BugAnalysis,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        res = crew.kickoff()
        data: BugAnalysis = res.pydantic

        if data is None:
            raise ValueError("Bug analysis did not return structured output.")

        self.state.triage_output = (
            f"**Severity:** {data.severity}\n"
            f"**Component:** {data.suspected_component}\n"
            f"**Action:** {data.immediate_action}\n"
            f"**Steps:**\n"
            + "\n".join(f"- {s}" for s in data.reproduction_steps)
        )

        return self.state.triage_output

    @listen("feature")
    def run_feature_crew(self):
        print("[3/4] Running Feature Crew...")

        agent = Agent(
            role="Product Manager",
            goal="Turn feature requests into user stories",
            backstory="Agile PM writing clear user stories.",
            llm=llm,
            verbose=True,
        )

        task = Task(
            description=(
                f"Create a user story for:\n"
                f"Title: {self.state.issue_title}\n"
                f"Body: {self.state.issue_body}"
            ),
            expected_output="Agile user story with acceptance criteria.",
            agent=agent,
            output_pydantic=FeatureStory,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        res = crew.kickoff()
        data: FeatureStory = res.pydantic

        if data is None:
            raise ValueError("Feature analysis did not return structured output.")

        self.state.triage_output = (
            f"**User Story:** {data.user_story}\n"
            f"**Criteria:**\n"
            + "\n".join(f"- {c}" for c in data.acceptance_criteria)
        )

        return self.state.triage_output

    @listen("question")
    def run_answer_crew(self):
        print("[3/4] Running Answer Crew with DuckDuckGo Search...")

        agent = Agent(
            role="Support Specialist",
            goal="Answer user queries using search",
            backstory="Technical documentation expert.",
            tools=[duckduckgo_search],
            llm=llm,
            verbose=True,
        )

        task = Task(
            description=(
                f"Answer this query using web search:\n"
                f"Title: {self.state.issue_title}\n"
                f"Body: {self.state.issue_body}"
            ),
            expected_output="Direct answer and reference sources.",
            agent=agent,
            output_pydantic=DocAnswer,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        res = crew.kickoff()
        data: DocAnswer = res.pydantic

        if data is None:
            raise ValueError("Question answer did not return structured output.")

        self.state.triage_output = (
            f"{data.direct_answer}\n\n"
            f"**Sources:**\n"
            + "\n".join(f"- {s}" for s in data.sources)
        )

        return self.state.triage_output

    @listen(or_(run_bug_crew, run_feature_crew, run_answer_crew))
    def post_reply(self, triage_result):
        print("\n[4/4] Formatting final reply...")

        self.state.final_reply = (
            f"### Triage Report\n"
            f"**Label:** `{self.state.classified_type.upper()}`\n\n"
            f"{triage_result}"
        )

        return self.state.final_reply


# 6. FUNCTION FOR FASTAPI
def run_bug_triage(issue_title: str, issue_body: str):

    if not issue_title.strip() or not issue_body.strip():
        raise ValueError("Both issue_title and issue_body are required.")

    flow = BugTriageFlow()

    output = flow.kickoff(
        inputs={
            "issue_title": issue_title,
            "issue_body": issue_body
        }
    )

    return output
