
import os

from crewai import Agent, Task, Crew, Process, LLM


def run_meeting_notes(transcript: str):

    # 1. Get Gemini API key from local environment
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in .env")

    # 2. Configure Gemini
    llm = LLM(
        model="gemini/gemini-3.1-flash-lite-preview",
        api_key=api_key
    )

    # 3. Validate transcript
    if not transcript or not transcript.strip():
        raise ValueError("Please provide a meeting transcript.")

    # 4. Save transcript locally
    os.makedirs("reports", exist_ok=True)

    with open("reports/transcript.txt", "w", encoding="utf-8") as file:
        file.write(transcript)

    # 5. Create Summarizer agent
    summarizer = Agent(
        role="Meeting Summarizer",
        goal="Create a clear summary of the meeting in exactly 5 lines.",
        backstory="You summarize meeting discussions accurately.",
        llm=llm,
        verbose=True
    )

    # 6. Create Action Finder agent
    action_finder = Agent(
        role="Action Item Finder",
        goal="Identify action items, their owners, and due dates.",
        backstory="You carefully extract tasks and deadlines from meetings.",
        llm=llm,
        verbose=True
    )

    # 7. Create Decision Logger agent
    decision_logger = Agent(
        role="Decision Logger",
        goal="List the important decisions made during the meeting.",
        backstory="You maintain accurate records of team decisions.",
        llm=llm,
        verbose=True
    )

    # 8. Create summary task
    summary_task = Task(
        description=(
            "Read this meeting transcript and write a summary in exactly "
            "5 lines:\n\n" + transcript
        ),
        expected_output="A meeting summary containing exactly 5 lines.",
        agent=summarizer,
        async_execution=True
    )

    # 9. Create action item task
    action_task = Task(
        description=(
            "Find every action item. Include the task, responsible person, "
            "and due date. Write 'Not specified' if a detail is missing.\n\n"
            + transcript
        ),
        expected_output="A list of action items, owners, and due dates.",
        agent=action_finder,
        async_execution=True
    )

    # 10. Create decision task
    decision_task = Task(
        description=(
            "Extract the decisions explicitly made in this meeting. "
            "Do not invent decisions.\n\n" + transcript
        ),
        expected_output="A list of confirmed meeting decisions.",
        agent=decision_logger,
        async_execution=True
    )

    # 11. Create Formatter agent
    formatter = Agent(
        role="Meeting Notes Formatter",
        goal="Combine the three task results into well-organized meeting notes.",
        backstory="You prepare professional, readable meeting records.",
        llm=llm,
        verbose=True
    )

    # 12. Create final formatting task
    format_task = Task(
        description="""
        Combine the results from the three previous tasks.

        Create Markdown notes with these sections:
        1. Meeting Summary
        2. Action Items (use a table with Task, Owner, Due Date)
        3. Decisions Made

        Do not invent missing information.
        """,
        expected_output="Complete meeting notes in Markdown format.",
        agent=formatter,
        context=[summary_task, action_task, decision_task]
    )

    # 13. Create Meeting Notes Crew
    meeting_crew = Crew(
        agents=[
            summarizer,
            action_finder,
            decision_logger,
            formatter
        ],
        tasks=[
            summary_task,
            action_task,
            decision_task,
            format_task
        ],
        process=Process.sequential,
        verbose=True
    )

    # 14. Run Crew synchronously
    result = meeting_crew.kickoff(
        inputs={"transcript": transcript}
    )

    # 15. Save final meeting notes
    report_path = "reports/meeting_notes.md"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(str(result))

    print("\nMeeting notes completed!")
    print(f"Report saved at: {report_path}")

    return str(result)
