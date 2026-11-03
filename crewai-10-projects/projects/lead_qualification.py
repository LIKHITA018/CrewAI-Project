
import os
import re
import csv
import urllib.request
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai.flow.flow import Flow, start, listen, router, or_


# -------------------------------------------------------------
# 1. LOCAL API KEY SETUP
# -------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from the .env file.")

os.environ["GEMINI_API_KEY1"] = api_key
os.environ.pop("OPENAI_API_KEY", None)

print("Gemini API key loaded.", flush=True)


# -------------------------------------------------------------
# 2. PYDANTIC STATE SCHEMA
# -------------------------------------------------------------

class LeadQualificationState(BaseModel):
    lead_name: str = ""
    lead_company: str = ""
    lead_website: str = ""
    website_content: str = ""
    enriched_summary: str = ""
    lead_score: str = ""
    action_summary: str = ""
    final_output: str = ""


# -------------------------------------------------------------
# 3. WEBSITE SCRAPER TOOL
# -------------------------------------------------------------

@tool("Scrape Website")
def scrape_website_tool(url: str) -> str:
    """Scrapes raw text from a company homepage."""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode(
                "utf-8", errors="ignore"
            )

            text = re.sub(r"<[^<]+?>", " ", html)
            cleaned = " ".join(text.split())

            return cleaned[:3000] if cleaned else "Empty page content."

    except Exception as e:
        return (
            f"Unable to reach website directly ({e}). "
            "Use available domain knowledge to evaluate."
        )


# -------------------------------------------------------------
# 4. LLM CONFIGURATION
# -------------------------------------------------------------

llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=api_key,
    temperature=0.2,
)


# -------------------------------------------------------------
# 5. LEAD QUALIFICATION FLOW
# -------------------------------------------------------------

class LeadQualificationFlow(Flow[LeadQualificationState]):

    @start()
    def capture_lead(self):
        """Captures initial inbound lead parameters."""

        print(
            f"\n[1/4] [Capture Lead] Processing "
            f"{self.state.lead_name} @ "
            f"{self.state.lead_company} "
            f"({self.state.lead_website})",
            flush=True
        )

        return {
            "name": self.state.lead_name,
            "company": self.state.lead_company,
            "website": self.state.lead_website
        }

    @listen(capture_lead)
    def enrich_lead(self, *args, **kwargs):
        """Scrapes the website and summarizes business offerings."""

        print(
            "[2/4] [Enrich Crew] Scraping company website...",
            flush=True
        )

        agent = Agent(
            role="Sales Intelligence Analyst",
            goal=(
                "Extract what the company does, its target market "
                "and product offerings."
            ),
            backstory=(
                "You research B2B websites to give sales reps "
                "immediate context."
            ),
            tools=[scrape_website_tool],
            llm=llm,
            function_calling_llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        task = Task(
            description=(
                f"Analyze the website for {self.state.lead_company} "
                f"at {self.state.lead_website}.\n"
                "Use the 'Scrape Website' tool to inspect the homepage.\n"
                "Provide a 3-sentence summary of:\n"
                "1. What product/service they sell\n"
                "2. Who their customers are\n"
                "3. Whether they look like an established enterprise, "
                "growing startup, or small hobbyist."
            ),
            expected_output="A 3-sentence company summary.",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=True
        )

        res = crew.kickoff()

        self.state.enriched_summary = res.raw

        return self.state.enriched_summary

    @router(enrich_lead)
    def score_lead(self, *args, **kwargs):
        """Classifies the lead as hot, warm or cold."""

        print(
            "[3/4] [Score Lead] Evaluating ICP fit...",
            flush=True
        )

        prompt = f"""
        Classify this lead into strictly one category:

        - 'hot': High value, clear B2B enterprise fit with budget/scale.
        - 'warm': Growing mid-market or startup that needs nurturing.
        - 'cold': Irrelevant domain, personal blog, or student.

        Company: {self.state.lead_company}
        Website: {self.state.lead_website}

        Enriched Info:
        {self.state.enriched_summary}

        Respond ONLY with a single word:
        'hot', 'warm', or 'cold'.
        """

        response = str(
            llm.call(
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        ).strip().lower()

        if "hot" in response:
            self.state.lead_score = "hot"

        elif "warm" in response:
            self.state.lead_score = "warm"

        else:
            self.state.lead_score = "cold"

        print(
            f"Decision: Lead scored as "
            f"{self.state.lead_score.upper()}",
            flush=True
        )

        return self.state.lead_score

    # ---------------------------------------------------------
    # BRANCH 1: HOT LEAD
    # ---------------------------------------------------------

    @listen("hot")
    def run_outreach_crew(self):

        print(
            "[Outreach Crew] Drafting personalized email...",
            flush=True
        )

        agent = Agent(
            role="Enterprise Account Executive",
            goal="Write a personalized, concise B2B cold outreach email.",
            backstory=(
                "You write high-converting executive emails tailored "
                "to the prospect's actual business."
            ),
            llm=llm,
            function_calling_llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True
        )

        task = Task(
            description=(
                f"Draft a personalized email to "
                f"{self.state.lead_name} at "
                f"{self.state.lead_company}.\n"
                f"Use this research:\n"
                f"{self.state.enriched_summary}\n\n"
                "Requirements:\n"
                "- Punchy subject line referencing their company\n"
                "- Specifically mention what they do\n"
                "- 1 clear value proposition\n"
                "- Friendly, low-friction CTA (15-min call)"
            ),
            expected_output="Personalized cold outreach email.",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=True
        )

        res = crew.kickoff()

        self.state.action_summary = (
            "**Status:** Hot Lead\n"
            "**Action:** Personalized Outreach Drafted\n\n"
            f"{res.raw}"
        )

        return self.state.action_summary

    # ---------------------------------------------------------
    # BRANCH 2: WARM LEAD
    # ---------------------------------------------------------

    @listen("warm")
    def add_to_nurture(self):

        print(
            "[Nurture Step] Enrolling in weekly tips sequence...",
            flush=True
        )

        self.state.action_summary = (
            "**Status:** Warm Lead\n"
            "**Action:** Enrolled in Weekly B2B Growth Newsletter\n"
            "- Segment: mid-market-prospects\n"
            "- Scheduled Email: "
            "'5 Ways to Automate Workflows in 2025'"
        )

        return self.state.action_summary

    # ---------------------------------------------------------
    # BRANCH 3: COLD LEAD
    # ---------------------------------------------------------

    @listen("cold")
    def archive_lead(self):

        print(
            "[Archive Step] Archiving cold lead...",
            flush=True
        )

        self.state.action_summary = (
            "**Status:** Cold Lead\n"
            "**Action:** Archived to CRM Archive\n"
            "- Reason: Below qualification criteria."
        )

        return self.state.action_summary

    # ---------------------------------------------------------
    # CONFLUENCE GATE
    # ---------------------------------------------------------

    @listen(
        or_(
            run_outreach_crew,
            add_to_nurture,
            archive_lead
        )
    )
    def log_lead(self, *args, **kwargs):
        """Appends the qualification decision to leads.csv."""

        print(
            "\n[4/4] [Log Lead] Writing entry to leads.csv...",
            flush=True
        )

        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        csv_file = reports_dir / "leads.csv"
        file_exists = csv_file.exists()

        with open(
            csv_file,
            mode="a",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            if not file_exists:
                writer.writerow([
                    "Timestamp",
                    "Lead Name",
                    "Company",
                    "Website",
                    "Score"
                ])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.state.lead_name,
                self.state.lead_company,
                self.state.lead_website,
                self.state.lead_score.upper()
            ])

        self.state.final_output = (
            "### Lead Qualification Summary\n\n"
            f"**Lead:** {self.state.lead_name} "
            f"({self.state.lead_company})\n"
            f"**Website:** {self.state.lead_website}\n"
            f"**Assigned Tier:** `{self.state.lead_score.upper()}`\n\n"
            f"{self.state.action_summary}\n\n"
            "---\n"
            "Saved to `reports/leads.csv`"
        )

        return self.state.final_output


# -------------------------------------------------------------
# 6. FUNCTION FOR FASTAPI
# -------------------------------------------------------------

def run_lead_qualification(
    lead_name: str,
    lead_company: str,
    lead_website: str
):

    if not lead_name.strip():
        raise ValueError("Lead name is required.")

    if not lead_company.strip():
        raise ValueError("Lead company is required.")

    if not lead_website.strip():
        raise ValueError("Lead website is required.")

    flow = LeadQualificationFlow()

    result = flow.kickoff(
        inputs={
            "lead_name": lead_name,
            "lead_company": lead_company,
            "lead_website": lead_website
        }
    )

    return {
        "result": str(result),
        "lead_score": flow.state.lead_score,
        "enriched_summary": flow.state.enriched_summary,
        "action_summary": flow.state.action_summary,
        "final_output": flow.state.final_output,
        "csv_file": str(ROOT_DIR / "reports" / "leads.csv")
    }
