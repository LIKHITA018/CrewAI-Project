
import os
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

from crewai import Agent, Task, Crew, Process, LLM
from ddgs import DDGS


# 1. Extract readable text from websites
class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style", "noscript", "svg"]:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ["script", "style", "noscript", "svg"] and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text.append(text)


# 2. Scrape a competitor website
def scrape_website(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            content_type = response.headers.get("Content-Type", "")

            if "text/html" not in content_type:
                return "The website did not return an HTML page."

            html = response.read(1_000_000).decode(
                "utf-8", errors="ignore"
            )

        parser = TextParser()
        parser.feed(html)

        return " ".join(parser.text)[:6000]

    except Exception as e:
        return f"Website scraping failed: {e}"


# 3. Search for competitor information using DDGS
def search_competitor(url):
    domain = urlparse(url).netloc.replace("www.", "")
    search_results = []

    queries = [
        f"site:{domain} pricing plans",
        f"site:{domain} products services features",
        f"{domain} latest news announcements"
    ]

    try:
        with DDGS() as ddgs:
            for query in queries:
                results = ddgs.text(query, max_results=3)

                for item in results:
                    search_results.append(
                        f"Title: {item.get('title', '')}\n"
                        f"Description: {item.get('body', '')}\n"
                        f"URL: {item.get('href', '')}"
                    )

    except Exception as e:
        search_results.append(f"DDGS search failed: {e}")

    return "\n\n".join(search_results)


# 4. Normalize and validate competitor URLs
def normalize_url(url):
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid competitor URL: {url}")

    return url


# 5. Main function called by FastAPI
def run_competitor_analysis(competitors: list[str]):

    # Read Gemini API key from environment
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your root .env file."
        )

    if len(competitors) != 3:
        raise ValueError("Please provide exactly 3 competitor URLs.")

    competitors = [normalize_url(url) for url in competitors]

    # Configure Gemini
    llm = LLM(
        model="gemini/gemini-3.1-flash-lite-preview",
        api_key=api_key,
        temperature=0.3
    )

    # 6. Research each competitor
    research_data = {}

    for url in competitors:
        domain = urlparse(url).netloc

        print(f"\nResearching {domain}...")

        website_text = scrape_website(url)
        search_text = search_competitor(url)

        research_data[url] = f"""
        WEBSITE: {url}

        WEBSITE CONTENT:
        {website_text}

        SEARCH RESULTS:
        {search_text}
        """

    # 7. Create specialist agents
    site_scraper = Agent(
        role="Site Scraper",
        goal="Analyze competitor website content and identify products and features",
        backstory="You extract useful business information from website content.",
        llm=llm,
        verbose=True
    )

    pricing_analyst = Agent(
        role="Pricing Analyst",
        goal="Compare competitor pricing, plans and value propositions",
        backstory="You specialize in competitive pricing research.",
        llm=llm,
        verbose=True
    )

    news_analyst = Agent(
        role="News Analyst",
        goal="Identify competitor announcements and recent developments",
        backstory="You analyze public news and market developments.",
        llm=llm,
        verbose=True
    )

    strategist = Agent(
        role="Business Strategist",
        goal="Prepare an evidence-based competitor SWOT analysis",
        backstory="You turn competitive research into actionable insights.",
        llm=llm,
        verbose=True
    )

    # 8. Create manager agent
    manager = Agent(
        role="Research Manager",
        goal="Coordinate the specialist agents and deliver a complete report",
        backstory="You manage competitive research and ensure findings are consistent.",
        llm=llm,
        allow_delegation=True,
        verbose=True
    )

    # 9. Create specialist tasks
    site_task = Task(
        description=f"""
        Analyze the following website research for all competitors.

        {research_data}

        Identify each competitor's:
        - Main products and services
        - Target customers
        - Key features
        - Differentiators

        Use only the supplied evidence and include source URLs.
        Mark missing information as unavailable.
        """,
        expected_output="Competitor website and product comparison.",
        agent=site_scraper
    )

    pricing_task = Task(
        description=f"""
        Compare pricing and plans for these competitors.

        {research_data}

        Identify published prices, plan names, included features
        and differences in value.

        Never invent prices. Clearly state when pricing is unavailable.
        Include source URLs.
        """,
        expected_output="A pricing comparison with evidence and source URLs.",
        agent=pricing_analyst
    )

    news_task = Task(
        description=f"""
        Analyze public announcements and news for these competitors.

        {research_data}

        Summarize relevant developments, partnerships, launches
        and market activity.

        Distinguish dated news from undated search results.
        Do not describe a result as recent without date evidence.
        Include source URLs.
        """,
        expected_output="A competitor news summary with sources and dates.",
        agent=news_analyst
    )

    strategy_task = Task(
        description=f"""
        Create a competitor analysis report for:

        {competitors}

        Use the outputs of the website, pricing and news analysis tasks.

        Include:
        1. Executive summary
        2. Competitor comparison table
        3. Product and feature comparison
        4. Pricing comparison
        5. Market and news insights
        6. SWOT analysis for each competitor
        7. Opportunities and recommendations
        8. Source URLs and research limitations

        Do not invent evidence, pricing or market-share figures.
        Separate verified observations from strategic inferences.
        Write the report in Markdown.
        """,
        expected_output="A complete evidence-based competitor report in Markdown.",
        agent=strategist,
        context=[site_task, pricing_task, news_task]
    )

    # 10. Create and run hierarchical Crew
    competitor_crew = Crew(
        agents=[
            site_scraper,
            pricing_analyst,
            news_analyst,
            strategist
        ],
        tasks=[
            site_task,
            pricing_task,
            news_task,
            strategy_task
        ],
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True
    )

    # Synchronous execution for FastAPI
    result = competitor_crew.kickoff()

    # 11. Save report locally
    os.makedirs("reports", exist_ok=True)

    filename = (
        "competitor_report_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".md"
    )

    report_path = os.path.join("reports", filename)

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(str(result))

    print("\nCompetitor analysis completed!")
    print(f"Report saved at: {report_path}")

    return str(result)
