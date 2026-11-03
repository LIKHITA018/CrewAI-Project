
import os
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel
from ddgs import DDGS

from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool

from crewai.flow import (
    Flow,
    start,
    listen,
    or_,
    router,
    human_feedback,
    HumanFeedbackProvider,
    HumanFeedbackPending,
    PendingFeedbackContext
)


# ============================================================
# 1. GEMINI API KEY SETUP
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT_DIR / ".env", override=True)

raw_key = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("GEMINI_API_KEY1")
    or ""
)

if not raw_key:
    raise ValueError("Gemini API key not found in .env file.")

cleaned_key_parts = [
    line.strip()
    for line in raw_key.replace("\r", "").split("\n")
    if line.strip()
]

unique_keys = list(dict.fromkeys(cleaned_key_parts))
api_key = unique_keys[0]

os.environ["GEMINI_API_KEY"] = api_key
os.environ["GEMINI_API_KEY1"] = api_key
os.environ.pop("OPENAI_API_KEY", None)

print("Gemini API key loaded successfully!")


# ============================================================
# 2. GEMINI MODEL CONFIGURATION
# ============================================================

llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=api_key,
    temperature=0.3
)


# ============================================================
# 3. FLOW STATE
# ============================================================

class ApprovalReportState(BaseModel):

    topic: str = ""
    audience: str = ""

    research_notes: str = ""
    draft: str = ""

    feedback: str = ""
    revision_count: int = 0

    status: str = "pending"
    final_report: str = ""
    report_file: str = ""


# ============================================================
# 4. DUCKDUCKGO SEARCH TOOL
# ============================================================

@tool("DuckDuckGo Web Search")
def duckduckgo_search(query: str) -> str:
    """Searches the web and returns relevant results with URLs."""

    try:
        results = DDGS().text(
            query,
            max_results=5
        )

        if not results:
            return "No search results found."

        formatted_results = []

        for item in results:

            title = item.get("title", "No title")
            body = item.get("body", "No description")
            url = item.get("href", "")

            formatted_results.append(
                f"""
                Title: {title}
                Description: {body}
                Source URL: {url}
                """
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Web search unavailable: {str(e)}"


# ============================================================
# 5. HUMAN FEEDBACK PROVIDER
# ============================================================

class APIReviewProvider(HumanFeedbackProvider):
    """Pauses the flow until feedback arrives through FastAPI."""

    def request_feedback(
        self,
        context: PendingFeedbackContext,
        flow: Flow
    ) -> str:

        print("\nHUMAN REVIEW REQUIRED")
        print("Flow ID:", context.flow_id)

        raise HumanFeedbackPending(
            context=context,
            callback_info={
                "review_endpoint": "/agent10/review"
            }
        )


review_provider = APIReviewProvider()


# ============================================================
# 6. APPROVAL REPORT FLOW
# ============================================================

class ApprovalReportFlow(Flow[ApprovalReportState]):

    # --------------------------------------------------------
    # STEP 1: COLLECT TOPIC
    # --------------------------------------------------------

    @start()
    def collect_topic(self):

        if not self.state.topic.strip():
            raise ValueError("Report topic cannot be empty.")

        if not self.state.audience.strip():
            self.state.audience = "General audience"

        print("\n" + "=" * 55)
        print("APPROVAL REPORT FLOW")
        print("=" * 55)

        print("TOPIC:", self.state.topic)
        print("AUDIENCE:", self.state.audience)

        return self.state.topic


    # --------------------------------------------------------
    # STEP 2: RESEARCH CREW - THREE AGENTS
    # --------------------------------------------------------

    @listen(collect_topic)
    def research_crew(self):

        print("\n[1/5] RESEARCH CREW ACTIVATED")

        researcher = Agent(
            role="Topic Research Specialist",
            goal=(
                "Collect accurate background information "
                "about the given topic."
            ),
            backstory=(
                "You are an expert researcher who finds "
                "reliable and relevant information."
            ),
            tools=[duckduckgo_search],
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        analyst = Agent(
            role="Industry and Trend Analyst",
            goal=(
                "Identify important developments, trends "
                "and practical examples."
            ),
            backstory=(
                "You analyze industry developments and "
                "identify important patterns."
            ),
            tools=[duckduckgo_search],
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        fact_checker = Agent(
            role="Fact Checking Specialist",
            goal=(
                "Verify important claims and identify "
                "reliable supporting sources."
            ),
            backstory=(
                "You are careful about accuracy, evidence "
                "and source credibility."
            ),
            tools=[duckduckgo_search],
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        task1 = Task(
            description=f"""
            Research the topic:

            {self.state.topic}

            Target audience:
            {self.state.audience}

            Search for:
            1. Introduction and background.
            2. Important definitions.
            3. Key concepts.
            4. Relevant facts and examples.

            Include source URLs.
            Do not invent information.
            """,
            expected_output=(
                "Detailed background research with source URLs."
            ),
            agent=researcher
        )

        task2 = Task(
            description=f"""
            Analyze the topic:

            {self.state.topic}

            Identify:
            1. Current developments and trends.
            2. Important applications.
            3. Benefits and opportunities.
            4. Challenges and limitations.
            5. Relevant real-world examples.

            Search for supporting sources and include URLs.
            """,
            expected_output=(
                "A detailed analysis of trends, applications "
                "and challenges with source URLs."
            ),
            agent=analyst
        )

        task3 = Task(
            description=f"""
            Fact-check the research about:

            {self.state.topic}

            Review the findings from the previous researchers.

            Identify:
            1. Important claims that need verification.
            2. Reliable supporting sources.
            3. Any conflicting information.
            4. Missing or uncertain information.

            Include source URLs.
            Clearly identify claims that cannot be verified.
            """,
            expected_output=(
                "A fact-checking report with verified claims "
                "and source URLs."
            ),
            agent=fact_checker
        )

        research_crew = Crew(
            agents=[
                researcher,
                analyst,
                fact_checker
            ],
            tasks=[
                task1,
                task2,
                task3
            ],
            process=Process.sequential,
            memory=False,
            verbose=True
        )

        result = research_crew.kickoff()

        self.state.research_notes = str(result.raw)

        print("\nRESEARCH COMPLETED!")

        return self.state.research_notes


    # --------------------------------------------------------
    # STEP 3: WRITING CREW
    # --------------------------------------------------------

    @listen(research_crew)
    def writing_crew(self):

        print("\n[2/5] WRITING CREW ACTIVATED")

        writer = Agent(
            role="Professional Report Writer",
            goal=(
                "Create a well-structured, accurate "
                "and informative report."
            ),
            backstory=(
                "You are an experienced technical and "
                "business report writer."
            ),
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        writing_task = Task(
            description=f"""
            Prepare a complete report on:

            TOPIC:
            {self.state.topic}

            TARGET AUDIENCE:
            {self.state.audience}

            RESEARCH MATERIAL:
            {self.state.research_notes}

            REPORT STRUCTURE:

            1. Title
            2. Executive Summary
            3. Introduction
            4. Background
            5. Main Discussion
            6. Important Findings
            7. Benefits and Applications
            8. Challenges and Limitations
            9. Conclusion
            10. References

            REQUIREMENTS:

            - Use clear professional language.
            - Organize the report using Markdown headings.
            - Use factual information from research.
            - Include source URLs in the references.
            - Do not invent statistics or citations.
            - Clearly mention information that could not
              be independently verified.
            """,
            expected_output=(
                "A complete professional Markdown report "
                "with references."
            ),
            agent=writer
        )

        writing_crew = Crew(
            agents=[writer],
            tasks=[writing_task],
            process=Process.sequential,
            memory=False,
            verbose=True
        )

        result = writing_crew.kickoff()

        self.state.draft = str(result.raw)

        print("\nFIRST REPORT DRAFT GENERATED!")

        return self.state.draft


    # --------------------------------------------------------
    # STEP 4A: APPROVED - PUBLISH REPORT
    # --------------------------------------------------------

    @listen("approved")
    def publish_report(self, result=None):

        print("\n[4/5] REPORT APPROVED!")

        self.state.status = "approved"
        self.state.final_report = self.state.draft

        filename = REPORTS_DIR / "final.md"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                f"# {self.state.topic}\n\n"
                f"**Target Audience:** {self.state.audience}\n\n"
                f"**Approval Status:** Approved\n\n"
                f"**Published On:** "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"---\n\n"
                f"{self.state.final_report}\n"
            )

        self.state.report_file = str(filename)

        print("\nREPORT SUCCESSFULLY PUBLISHED!")
        print("Saved as:", filename)

        return {
            "status": "approved",
            "report_file": str(filename)
        }


    # --------------------------------------------------------
    # STEP 4B: REVISION CREW
    # --------------------------------------------------------

    @listen("revise")
    def revision_crew(self, result=None):

        print("\n[REVISION] REVISION CREW ACTIVATED")

        self.state.revision_count += 1

        latest_feedback = self.state.feedback

        if not latest_feedback:
            latest_feedback = "Improve the report."

        print("\nREVIEWER FEEDBACK:")
        print(latest_feedback)

        reviser = Agent(
            role="Report Revision Specialist",
            goal=(
                "Improve the report according to the "
                "reviewer's feedback."
            ),
            backstory=(
                "You are an expert editor who improves "
                "accuracy, clarity, structure and completeness."
            ),
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        revision_task = Task(
            description=f"""
            Revise the following report.

            TOPIC:
            {self.state.topic}

            TARGET AUDIENCE:
            {self.state.audience}

            CURRENT REPORT:
            {self.state.draft}

            HUMAN REVIEWER FEEDBACK:
            {latest_feedback}

            INSTRUCTIONS:

            1. Carefully understand the feedback.
            2. Make the requested corrections.
            3. Improve clarity and organization.
            4. Preserve useful existing information.
            5. Do not invent facts or references.
            6. Keep source URLs in the references.
            7. Return the COMPLETE revised report in Markdown.

            This is revision number:
            {self.state.revision_count}
            """,
            expected_output=(
                "The complete revised report in Markdown format."
            ),
            agent=reviser
        )

        revision_crew = Crew(
            agents=[reviser],
            tasks=[revision_task],
            process=Process.sequential,
            memory=False,
            verbose=True
        )

        result = revision_crew.kickoff()

        self.state.draft = str(result.raw)

        print("\nREPORT REVISED SUCCESSFULLY!")
        print("Revision count:", self.state.revision_count)

        return self.state.draft


    # --------------------------------------------------------
    # STEP 5: HUMAN REVIEW
    # --------------------------------------------------------

    @human_feedback(
        message=(
            "\nREVIEW THE REPORT ABOVE.\n"
            "Type APPROVE if the report is ready to publish.\n"
            "Type REVISE: followed by your requested changes "
            "if the report needs improvement."
        ),
        provider=review_provider
    )
    @listen(or_(writing_crew, revision_crew))
    def review_draft(self):

        print("\n[3/5] HUMAN REVIEW")
        print("Report version:", self.state.revision_count + 1)

        return self.state.draft


    # --------------------------------------------------------
    # STEP 5B: DIRECT PYTHON FEEDBACK ROUTER
    # --------------------------------------------------------

    @router("review_draft")
    def route_review(self, result):

        feedback = str(
            getattr(result, "feedback", "")
            or ""
        ).strip()

        normalized = feedback.lower().strip()

        print("\nREVIEWER DECISION:", feedback)

        # Reject negative approval phrases first
        negative_phrases = [
            "do not approve",
            "don't approve",
            "not approved",
            "not approve",
            "needs revision"
        ]

        if any(
            phrase in normalized
            for phrase in negative_phrases
        ):
            self.state.feedback = feedback
            return "revise"

        # Direct approval
        approval_phrases = [
            "approve",
            "approved",
            "publish",
            "accept",
            "looks good"
        ]

        if any(
            phrase in normalized
            for phrase in approval_phrases
        ):
            self.state.feedback = ""
            return "approved"

        # Revision request
        revision_phrases = [
            "revise",
            "revision",
            "improve",
            "change",
            "modify",
            "update"
        ]

        if any(
            phrase in normalized
            for phrase in revision_phrases
        ):

            if normalized.startswith("revise"):
                feedback = re.sub(
                    r"^revise\s*:?\s*",
                    "",
                    feedback,
                    flags=re.IGNORECASE
                ).strip()

            self.state.feedback = (
                feedback or "Improve the report."
            )

            return "revise"

        # Unclear feedback: safely request revision
        self.state.feedback = (
            feedback or "Please improve the report."
        )

        return "revise"


# ============================================================
# 7. START APPROVAL REPORT FLOW
# ============================================================

def run_approval_report(topic: str, audience: str):

    if not topic or not topic.strip():
        raise ValueError("Report topic cannot be empty.")

    flow = ApprovalReportFlow()

    flow.state.topic = topic.strip()

    flow.state.audience = (
        audience.strip()
        if audience and audience.strip()
        else "General audience"
    )

    result = flow.kickoff()

    if isinstance(result, HumanFeedbackPending):

        return {
            "status": "pending_review",
            "flow_id": result.context.flow_id,
            "topic": flow.state.topic,
            "audience": flow.state.audience,
            "draft": result.context.method_output,
            "revision_count": flow.state.revision_count,
            "message": (
                "Report generated. Review it and submit "
                "APPROVE or REVISE through /agent10/review."
            )
        }

    return {
        "status": flow.state.status,
        "topic": flow.state.topic,
        "audience": flow.state.audience,
        "revision_count": flow.state.revision_count,
        "report_file": flow.state.report_file
    }


# ============================================================
# 8. RESUME APPROVAL FLOW
# ============================================================

def review_approval_report(flow_id: str, feedback: str):

    if not flow_id or not flow_id.strip():
        raise ValueError("Flow ID cannot be empty.")

    if not feedback or not feedback.strip():
        raise ValueError("Review feedback cannot be empty.")

    flow = ApprovalReportFlow.from_pending(
        flow_id.strip()
    )

    result = flow.resume(feedback.strip())

    if isinstance(result, HumanFeedbackPending):

        return {
            "status": "pending_review",
            "flow_id": result.context.flow_id,
            "topic": flow.state.topic,
            "audience": flow.state.audience,
            "draft": result.context.method_output,
            "revision_count": flow.state.revision_count,
            "message": (
                "The report has been revised. Please review "
                "the new draft and submit your decision again."
            )
        }

    return {
        "status": flow.state.status,
        "topic": flow.state.topic,
        "audience": flow.state.audience,
        "revision_count": flow.state.revision_count,
        "report_file": flow.state.report_file,
        "message": (
            "Report approved and published."
            if flow.state.status == "approved"
            else "Flow completed."
        )
    }
