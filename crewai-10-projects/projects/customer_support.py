
import os
import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel
from crewai import LLM
from crewai.flow.flow import Flow, start, listen, router, or_

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Gemini connection
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=api_key
)


# 1. Define ticket state
class SupportTicketState(BaseModel):
    ticket_id: str = "TICKET-101"
    customer_name: str = "Rahul"
    issue_description: str = (
        "I was charged twice for my monthly subscription."
    )
    category: str = ""
    priority: str = ""
    resolution: str = ""


# 2. Create customer support flow
class CustomerSupportFlow(Flow[SupportTicketState]):

    @start()
    def receive_ticket(self):
        print("\n1. RECEIVED TICKET")
        print("Ticket ID:", self.state.ticket_id)
        print("Customer:", self.state.customer_name)
        print("Issue:", self.state.issue_description)

    @listen(receive_ticket)
    def categorize_ticket(self):
        print("\n2. CATEGORIZING TICKET...")

        prompt = f"""
        Categorize this customer support ticket.

        Issue: {self.state.issue_description}

        Choose exactly one category:
        billing, account_access, other

        Choose priority: high, medium, low.

        Return ONLY valid JSON:
        {{
            "category": "billing",
            "priority": "high"
        }}
        """

        response = llm.call(prompt)

        text = str(response).strip()
        text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)

        allowed_categories = {
            "billing", "account_access", "other"
        }
        allowed_priorities = {"high", "medium", "low"}

        category = data.get("category", "").lower()
        priority = data.get("priority", "medium").lower()

        if category not in allowed_categories:
            category = "other"

        if priority not in allowed_priorities:
            priority = "medium"

        self.state.category = category
        self.state.priority = priority

        print("Category:", self.state.category)
        print("Priority:", self.state.priority)

    @router(categorize_ticket)
    def route_by_category(self) -> Literal[
        "billing", "account_access", "other"
    ]:

        print("\n3. ROUTING TICKET...")

        if self.state.category == "billing":
            return "billing"
        elif self.state.category == "account_access":
            return "account_access"
        else:
            return "other"

    @listen("billing")
    def handle_billing(self):
        self.state.resolution = (
            "Billing team: verify the duplicate charge, "
            "check the transaction records, and initiate a refund "
            "if the duplicate payment is confirmed."
        )
        print("Billing handler selected.")

    @listen("account_access")
    def handle_access(self):
        self.state.resolution = (
            "Account support: verify the customer's identity "
            "and guide them through password recovery or account access."
        )
        print("Account access handler selected.")

    @listen("other")
    def handle_other(self):
        self.state.resolution = (
            "Technical support: investigate the reported issue, "
            "collect relevant error details, and provide troubleshooting."
        )
        print("General support handler selected.")

    @listen(or_(handle_billing, handle_access, handle_other))
    def resolve_ticket(self):

        print("\n4. FINAL SUPPORT RESULT")

        result = {
            "ticket_id": self.state.ticket_id,
            "customer_name": self.state.customer_name,
            "category": self.state.category,
            "priority": self.state.priority,
            "resolution": self.state.resolution
        }

        print(json.dumps(result, indent=2))
        return result


# 3. Function called by FastAPI
def run_customer_support(
    ticket_id="TICKET-101",
    customer_name="Rahul",
    issue_description="I was charged twice for my monthly subscription."
):

    flow = CustomerSupportFlow()

    flow.state.ticket_id = ticket_id
    flow.state.customer_name = customer_name
    flow.state.issue_description = issue_description

    result = flow.kickoff()

    REPORTS_DIR.mkdir(exist_ok=True)

    output_path = REPORTS_DIR / "support_result.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return result
