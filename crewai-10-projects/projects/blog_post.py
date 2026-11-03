
import os
from crewai import Agent, Task, Crew, Process, LLM
from ddgs import DDGS



def run_blog_post(topic: str):

    # 1. Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    llm = LLM(
        model="gemini/gemini-3.1-flash-lite-preview",
        api_key=api_key,
        temperature=0.4
    )

    # 2. Search the web
    def search_web(topic):
        results = DDGS().text(topic, max_results=5)
        research = []

        for item in results:
            research.append(
                f"Title: {item.get('title', '')}\n"
                f"Description: {item.get('body', '')}\n"
                f"URL: {item.get('href', '')}"
            )

        return "\n\n".join(research)

    try:
        research_data = search_web(topic)
    except Exception as e:
        print("Search failed:", e)
        research_data = (
            "No web search results available. "
            "Avoid unsupported factual claims."
        )

    # 3. Create agents
    researcher = Agent(
        role="Researcher",
        goal="Analyze search results and identify useful facts",
        backstory="You are a careful web researcher.",
        llm=llm,
        verbose=True
    )

    writer = Agent(
        role="Blog Writer",
        goal="Write an engaging blog post of approximately 600 words",
        backstory="You write clear, informative blog posts.",
        llm=llm,
        verbose=True
    )

    editor = Agent(
        role="Editor",
        goal="Polish the blog post and check factual consistency",
        backstory="You are an experienced editor.",
        llm=llm,
        verbose=True
    )

    # 4. Create tasks
    research_task = Task(
        description=f"""
        Research topic: {topic}

        Analyze these DDGS search results:
        {research_data}

        Identify key facts, benefits, challenges and examples.
        Keep source URLs and do not invent facts.
        """,
        expected_output="Research notes with facts and source URLs.",
        agent=researcher
    )

    writing_task = Task(
        description=f"""
        Write a blog post about {topic} using the research.

        Include a title, introduction, headings, examples,
        benefits, challenges and conclusion.

        Write approximately 600 words in Markdown.
        Preserve relevant source URLs.
        """,
        expected_output="A complete Markdown blog post.",
        agent=writer,
        context=[research_task]
    )

    editing_task = Task(
        description="""
        Edit the blog post for grammar, clarity, structure
        and factual consistency.

        Preserve useful source URLs.
        Return only the final polished blog post in Markdown.
        """,
        expected_output="A polished final blog post in Markdown.",
        agent=editor,
        context=[research_task, writing_task]
    )

    # 5. Create Crew
    blog_crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, writing_task, editing_task],
        process=Process.sequential,
        verbose=True
    )

    # 6. Run Crew
    result = blog_crew.kickoff()

    # 7. Return output to FastAPI
    return str(result)


def agent1(data: dict):
    topic = data.get("input")

    if not topic:
        return {"error": "Please provide a blog topic"}

    result = run_blog_post(topic)

    return {"output": result}