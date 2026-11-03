
import os
import json
from pathlib import Path

import pandas as pd
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

SALES_CSV_PATH = REPORTS_DIR / "sales.csv"


# 1. Custom Pandas analysis tool
@tool("Sales CSV Analyzer")
def analyze_sales_csv(query: str) -> str:
    """
    Read sales.csv and return actual statistics and sales totals.
    Use this tool to retrieve numerical facts for the report.
    """

    data = pd.read_csv(SALES_CSV_PATH)

    summary = {
        "rows": int(len(data)),
        "columns": list(data.columns),
        "missing_values": {
            k: int(v)
            for k, v in data.isnull().sum().items()
        },
        "numeric_statistics": json.loads(
            data.select_dtypes(include="number")
            .describe()
            .round(2)
            .to_json()
        ),
        "total_sales": float(data["Sales"].sum()),
        "average_sale": round(float(data["Sales"].mean()), 2),
        "sales_by_product": {
            k: float(v)
            for k, v in data.groupby("Product")["Sales"].sum().items()
        },
        "quantity_by_product": {
            k: int(v)
            for k, v in data.groupby("Product")["Quantity"].sum().items()
        }
    }

    return json.dumps(summary, indent=2)


# 2. Main project function
def run_data_report():

    # Load Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your root .env file."
        )

    llm = LLM(
        model="gemini/gemini-3.1-flash-lite-preview",
        api_key=api_key
    )

    # 3. Create sample sales.csv
    sales_data = {
        "Date": [
            "2026-10-01", "2026-10-02", "2026-10-03",
            "2026-10-04", "2026-10-05", "2026-10-06",
            "2026-10-07", "2026-10-08"
        ],
        "Product": [
            "Laptop", "Phone", "Laptop", "Tablet",
            "Phone", "Tablet", "Laptop", "Phone"
        ],
        "Quantity": [2, 5, 1, 4, 3, 6, 2, 4],
        "Price": [
            50000, 20000, 50000, 15000,
            20000, 15000, 50000, 20000
        ]
    }

    df = pd.DataFrame(sales_data)
    df["Sales"] = df["Quantity"] * df["Price"]

    df.to_csv(SALES_CSV_PATH, index=False)

    print("sales.csv created successfully!")
    print(df.head())

    # 4. Agent 1: Data Analyst
    analyst = Agent(
        role="Data Analyst",
        goal="Calculate accurate statistics from the sales CSV.",
        backstory="You are skilled at pandas and numerical data analysis.",
        tools=[analyze_sales_csv],
        llm=llm,
        verbose=True
    )

    # 5. Agent 2: Insight Writer
    writer = Agent(
        role="Insight Writer",
        goal="Explain the three most important findings from sales data.",
        backstory="You turn data into clear and useful business insights.",
        llm=llm,
        verbose=True
    )

    # 6. Agent 3: Reviewer
    reviewer = Agent(
        role="Report Reviewer",
        goal="Check every reported number against the analyst's results.",
        backstory=(
            "You are careful about numerical accuracy "
            "and unsupported claims."
        ),
        llm=llm,
        verbose=True
    )

    # 7. Create tasks
    analysis_task = Task(
        description="""
        Analyze sales.csv using the Sales CSV Analyzer tool.
        Include the row count, missing values, total sales,
        average sale, and sales by product.
        Use the tool's actual results; do not guess numbers.
        """,
        expected_output=(
            "A structured report of verified sales statistics."
        ),
        agent=analyst
    )

    insight_task = Task(
        description="""
        Use the analyst's results to identify the top three findings.
        Explain which product generated the highest sales and why
        the findings matter. Do not invent data.
        """,
        expected_output="Three evidence-based business insights.",
        agent=writer,
        context=[analysis_task]
    )

    review_task = Task(
        description="""
        Review the statistics and insights against the analyst's results.
        Correct unsupported claims or inconsistent numbers.
        Return the corrected findings and a clear review note.
        """,
        expected_output=(
            "Reviewed findings with numerical accuracy checked."
        ),
        agent=reviewer,
        context=[analysis_task, insight_task]
    )

    # 8. Run the Crew
    data_crew = Crew(
        agents=[analyst, writer, reviewer],
        tasks=[analysis_task, insight_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    result = data_crew.kickoff()

    # 9. Prepare final report
    analysis_output = (
        analysis_task.output.raw if analysis_task.output else ""
    )

    insight_output = (
        insight_task.output.raw if insight_task.output else ""
    )

    review_output = (
        review_task.output.raw if review_task.output else ""
    )

    report = f"""# Weekly Sales Report

## 1. Data Analysis

{analysis_output}

## 2. Top Three Insights

{insight_output}

## 3. Review and Validation

{review_output}
"""

    # 10. Save report
    report_path = REPORTS_DIR / "data_report.md"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report)

    print("\n===== FINAL REPORT =====\n")
    print(report)
    print(f"\nReport saved at: {report_path}")

    return report
