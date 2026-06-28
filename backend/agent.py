import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools import search_members, analyze_performance, get_recommendations

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat_history = []

SYSTEM_PROMPT = """
You are an intelligent AI Agent for TechNova Club 
at Karpagam College of Engineering.
You have access to real club data.
Always give clear, structured, helpful answers.
Be specific with names, scores, and achievements.
"""

def run_agent(user_question: str) -> str:

    tool_data = ""
    question_lower = user_question.lower()

    if any(word in question_lower for word in
           ["who is", "find", "search", "member",
            "president", "leader", "skill", "யாரு"]):
        tool_data += "\nMEMBER SEARCH RESULTS:\n"
        tool_data += search_members(user_question)

    if any(word in question_lower for word in
           ["perform", "attendance", "active",
            "inactive", "score", "top", "best"]):
        tool_data += "\nPERFORMANCE ANALYSIS:\n"
        if "inactive" in question_lower:
            tool_data += analyze_performance("inactive")
        elif "top" in question_lower or "best" in question_lower:
            tool_data += analyze_performance("top")
        else:
            tool_data += analyze_performance("all")

    if any(word in question_lower for word in
           ["recommend", "suggest", "next",
            "summary", "overview", "suitable"]):
        tool_data += "\nRECOMMENDATIONS:\n"
        if "president" in question_lower:
            tool_data += get_recommendations("next_president")
        elif "inactive" in question_lower or "engage" in question_lower:
            tool_data += get_recommendations("engage_inactive")
        elif "summary" in question_lower or "overview" in question_lower:
            tool_data += get_recommendations("club_summary")
        else:
            tool_data += get_recommendations("best_performer")

    if not tool_data:
        tool_data = get_recommendations("club_summary")

    chat_history.append({
        "role": "user",
        "content": user_question
    })

    full_message = f"""
    User Question: {user_question}
    
    Real Club Data from Database:
    {tool_data}
    
    Based on this real data, provide a helpful,
    clear and insightful answer.
    """

    messages_to_send = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + chat_history[:-1] + [{
        "role": "user",
        "content": full_message
    }]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_to_send,
        max_tokens=1000
    )

    answer = response.choices[0].message.content

    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    return answer


if __name__ == "__main__":
    print("TechNova Club AI Agent Testing...\n")

    questions = [
        "Who is the president of the club?",
        "Who is the best performer?",
        "Who are the inactive members?",
        "Who is suitable for next president?"
    ]

    for q in questions:
        print(f"Q: {q}")
        print(f"A: {run_agent(q)}")
        print("-" * 50)