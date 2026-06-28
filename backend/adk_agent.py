import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools import search_members, analyze_performance, get_recommendations

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not set. Add it to your .env file like:\nGROQ_API_KEY=your_actual_groq_key_here"
    )
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADK Tools
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def search_club_members(query: str) -> dict:
    """
    Search for club members by name, role, skills, or any query.
    Use this when asked about specific members, roles, or skills.
    Args:
        query: Search query about members
    Returns:
        Member details from database
    """
    result = search_members(query)
    return {"result": result}


def analyze_club_performance(filter_type: str) -> dict:
    """
    Analyze club member performance and attendance.
    Use this when asked about performance, attendance, rankings.
    Args:
        filter_type: "all", "top", "active", or "inactive"
    Returns:
        Performance analysis data
    """
    result = analyze_performance(filter_type)
    return {"result": result}


def get_club_recommendations(recommendation_type: str) -> dict:
    """
    Get smart recommendations for club decisions.
    Use this when asked for recommendations, suggestions, or summaries.
    Args:
        recommendation_type: "next_president", "engage_inactive",
                            "best_performer", or "club_summary"
    Returns:
        Recommendations based on club data
    """
    result = get_recommendations(recommendation_type)
    return {"result": result}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADK Agent (now powered by Groq via LiteLLM instead of Gemini)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

club_agent = Agent(
    name="TechNovaClubAgent",
    model=LiteLlm(model="groq/llama-3.1-8b-instant"),
    description="Intelligent AI Agent for TechNova Club at Karpagam College of Engineering.",
    instruction="""
        You are TechNova Club AI Agent at Karpagam College of Engineering —
        a friendly, conversational assistant, not a data-dumping bot.

        IMPORTANT BEHAVIOR RULES:
        - If the user sends a greeting (hi, hello, hey, vanakkam, etc.) or small talk,
          reply warmly and briefly, and ask what they'd like to know about the club.
          Do NOT call any tool and do NOT mention members, scores, or data unless asked.
        - Only call a tool when the question actually requires club data
          (members, performance, attendance, recommendations, summaries).
        - Use the right tool for the right question:
          - search_club_members: member details, roles, skills
          - analyze_club_performance: performance, attendance, rankings
          - get_club_recommendations: recommendations, summaries
        - Keep answers focused on exactly what was asked — don't volunteer
          extra unrelated stats just because you have the data available.

        Answer in the same language style as the question:
        - English → English
        - Tamil → Tamil
        - Tanglish → Tanglish

        When you do answer with data, be specific with names, scores, and achievements.
    """,
    tools=[
        search_club_members,
        analyze_club_performance,
        get_club_recommendations
    ]
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Async Runner
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APP_NAME = "TechNovaClub"
USER_ID = "user_001"
SESSION_ID = "session_001"

# Created ONCE at module load (not per-question). This is what gives the
# agent memory across questions in the same chat -- e.g. "Rahul yaaru?" then
# "avan events enna?" will carry context, instead of every question being
# treated as a brand new, isolated conversation.
session_service = InMemorySessionService()
_session_ready = False

runner = Runner(
    agent=club_agent,
    app_name=APP_NAME,
    session_service=session_service
)

async def _run_once(user_question: str) -> str:
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_question)]
    )

    final_answer = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_answer = event.content.parts[0].text

    return final_answer if final_answer else "Sorry, could not process that."


async def run_adk_agent_async(user_question: str, _retries: int = 2) -> str:
    global _session_ready
    try:
        if not _session_ready:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=SESSION_ID
            )
            _session_ready = True

        last_error = None
        for attempt in range(_retries + 1):
            try:
                return await _run_once(user_question)
            except Exception as e:
                # Groq/LiteLLM sometimes emits a malformed tool-call
                # (<function=name,{json}> instead of a proper structured
                # call), which the API then rejects with tool_use_failed.
                # This is a model-generation quirk, not a code bug -- retrying
                # the same question usually produces a valid tool call.
                if "tool_use_failed" in str(e) or "tool call validation failed" in str(e):
                    last_error = e
                    continue
                return f"Error: {str(e)}"

        return f"Error: {str(last_error)}"

    except Exception as e:
        return f"Error: {str(e)}"


def run_adk_agent(user_question: str) -> str:
    return asyncio.run(run_adk_agent_async(user_question))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("TechNova Club ADK Agent Testing...\n")

    questions = [
        "Who is the president of the club?",
        "Who is the best performer?",
        "Who are the inactive members?",
        "Next president ku yaaru suitable?"
    ]

    for q in questions:
        print(f"Q: {q}")
        print(f"A: {run_adk_agent(q)}")
        print("-" * 50)