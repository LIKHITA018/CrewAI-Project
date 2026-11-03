
import os
import re
import urllib.request
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.flow.flow import Flow, start, listen, and_


# 1. API KEY SETUP
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Disable accidental OpenAI fallback
os.environ.pop("OPENAI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = api_key


# 2. SCHEMAS
class LinkedInPost(BaseModel):
    hook: str = Field(description="Attention-grabbing first line")
    body: str = Field(description="Core post content, roughly 150 words")
    call_to_action: str = Field(description="Discussion CTA")
    hashtags: List[str] = Field(description="3-5 hashtags")


class TwitterThread(BaseModel):
    tweets: List[str] = Field(
        description="List of 6 numbered tweets, each under 280 chars"
    )


class NewsletterDraft(BaseModel):
    subject_line: str = Field(description="Catchy email subject line")
    intro: str = Field(description="Introductory paragraph")
    bullet_points: List[str] = Field(
        description="Exactly 3 key actionable takeaways"
    )
    closing_takeaway: str = Field(description="Final thought")


class ContentRepurposingState(BaseModel):
    article_input: str = ""
    article_text: str = ""
    extracted_points: str = ""
    linkedin_content: str = ""
    twitter_content: str = ""
    newsletter_content: str = ""
    saved_files: List[str] = []


# 3. LLM CONFIGURATION
llm = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    api_key=api_key,
    temperature=0.4,
)


# 4. CONTENT REPURPOSING FLOW
class ContentRepurposingFlow(Flow[ContentRepurposingState]):

    @start()
    def load_article(self):
        print("\n[1/4] Loading article...")

        src = self.state.article_input.strip()

        if src.startswith("http://") or src.startswith("https://"):
            try:
                req = urllib.request.Request(
                    src,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                with urllib.request.urlopen(req, timeout=10) as response:
                    clean_text = re.sub(
                        r"<[^<]+?>",
                        " ",
                        response.read().decode(
                            "utf-8", errors="ignore"
                        )
                    )

                    self.state.article_text = (
                        " ".join(clean_text.split())[:8000]
                    )

            except Exception as e:
                print(f"URL fetch failed ({e}), using direct text.")
                self.state.article_text = src

        elif os.path.exists(src):
            with open(src, "r", encoding="utf-8") as f:
                self.state.article_text = f.read()

        else:
            self.state.article_text = src

        print(
            f"Article loaded "
            f"({len(self.state.article_text.split())} words)."
        )

        return self.state.article_text

    @listen(load_article)
    def extract_points(self):
        print("[2/4] Extracting key insights using Direct LLM call...")

        prompt = (
            "Read the following article and extract the top 5 core "
            "insights, key metrics, and practical takeaways.\n"
            "Format as clear bullet points.\n\n"
            f"Article:\n{self.state.article_text[:6000]}"
        )

        response = llm.call(
            messages=[{"role": "user", "content": prompt}]
        )

        self.state.extracted_points = response

        print("Key points extracted successfully.")

        return self.state.extracted_points

    # PARALLEL CREW 1: LINKEDIN
    @listen(extract_points)
    def run_linkedin_crew(self):
        print("[LinkedIn Crew] Drafting post...")

        agent = Agent(
            role="LinkedIn Content Strategist",
            goal="Write an engaging ~150-word LinkedIn post",
            backstory="You write viral B2B LinkedIn posts using strong hooks.",
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True,
        )

        task = Task(
            description=(
                "Transform these points into a LinkedIn post:\n"
                f"{self.state.extracted_points}"
            ),
            expected_output=(
                "Structured LinkedIn post with hook, ~150 word body, "
                "CTA, and hashtags."
            ),
            agent=agent,
            output_pydantic=LinkedInPost,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=True
        )

        res = crew.kickoff()
        data: LinkedInPost = res.pydantic

        if data is None:
            raise ValueError("LinkedIn crew returned no structured output.")

        formatted = (
            f"{data.hook}\n\n"
            f"{data.body}\n\n"
            f"{data.call_to_action}\n\n"
            f"{' '.join('#' + h.strip('#') for h in data.hashtags)}"
        )

        self.state.linkedin_content = formatted

        return formatted

    # PARALLEL CREW 2: TWITTER
    @listen(extract_points)
    def run_twitter_crew(self):
        print("[Twitter Crew] Drafting 6-tweet thread...")

        agent = Agent(
            role="Twitter Ghostwriter",
            goal="Create a 6-tweet thread explaining complex ideas simply",
            backstory="You write viral tech threads with high engagement.",
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True,
        )

        task = Task(
            description=(
                "Convert these insights into exactly 6 tweets:\n"
                f"{self.state.extracted_points}"
            ),
            expected_output=(
                "List of 6 numbered tweets under 280 characters each."
            ),
            agent=agent,
            output_pydantic=TwitterThread,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=True
        )

        res = crew.kickoff()
        data: TwitterThread = res.pydantic

        if data is None:
            raise ValueError("Twitter crew returned no structured output.")

        formatted = "\n\n---\n\n".join(data.tweets)

        self.state.twitter_content = formatted

        return formatted

    # PARALLEL CREW 3: NEWSLETTER
    @listen(extract_points)
    def run_newsletter_crew(self):
        print("[Newsletter Crew] Drafting email edition...")

        agent = Agent(
            role="Newsletter Editor",
            goal="Craft an executive newsletter section with intro and 3 takeaways",
            backstory="You edit a high-converting weekly tech newsletter.",
            llm=llm,
            memory=False,
            allow_delegation=False,
            verbose=True,
        )

        task = Task(
            description=(
                "Draft a newsletter edition using these key points:\n"
                f"{self.state.extracted_points}"
            ),
            expected_output=(
                "Subject line, intro paragraph, and 3 key bullets."
            ),
            agent=agent,
            output_pydantic=NewsletterDraft,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=True
        )

        res = crew.kickoff()
        data: NewsletterDraft = res.pydantic

        if data is None:
            raise ValueError("Newsletter crew returned no structured output.")

        bullets_formatted = "\n".join(
            f"- {b}" for b in data.bullet_points
        )

        formatted = (
            f"Subject: {data.subject_line}\n\n"
            f"{data.intro}\n\n"
            f"**Key Takeaways:**\n{bullets_formatted}\n\n"
            f"{data.closing_takeaway}"
        )

        self.state.newsletter_content = formatted

        return formatted

    # CONFLUENCE GATE: WAIT FOR ALL THREE CREWS
    @listen(and_(
        run_linkedin_crew,
        run_twitter_crew,
        run_newsletter_crew
    ))
    def publish_pack(self, *args, **kwargs):
        print("\n[4/4] All 3 crews finished! Saving 3 files...")

        output_dir = ROOT_DIR / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        linkedin_path = output_dir / "linkedin_post.md"
        twitter_path = output_dir / "twitter_thread.md"
        newsletter_path = output_dir / "newsletter.md"

        with open(linkedin_path, "w", encoding="utf-8") as f:
            f.write(self.state.linkedin_content)

        with open(twitter_path, "w", encoding="utf-8") as f:
            f.write(self.state.twitter_content)


        with open(newsletter_path, "w", encoding="utf-8") as f:
            f.write(self.state.newsletter_content)

        self.state.saved_files = [
            str(linkedin_path),
            str(twitter_path),
            str(newsletter_path)
        ]

        return (
            "Content Repurposing Pack Published!\n\n"
            "Saved files:\n"
            f"- {linkedin_path}\n"
            f"- {twitter_path}\n"
            f"- {newsletter_path}\n\n"
            "================ PREVIEWS ================\n\n"
            f"LinkedIn:\n{self.state.linkedin_content[:250]}...\n\n"
            f"Twitter Thread:\n{self.state.twitter_content[:250]}...\n\n"
            f"Newsletter:\n{self.state.newsletter_content[:250]}...\n"
        )


# 5. FUNCTION FOR FASTAPI
def run_content_repurposing(article_input: str):

    if not article_input.strip():
        raise ValueError("Article text or URL is required.")

    flow = ContentRepurposingFlow()

    result = flow.kickoff(
        inputs={"article_input": article_input}
    )

    return {
        "result": result,
        "saved_files": flow.state.saved_files,
        "linkedin_content": flow.state.linkedin_content,
        "twitter_content": flow.state.twitter_content,
        "newsletter_content": flow.state.newsletter_content
    }
