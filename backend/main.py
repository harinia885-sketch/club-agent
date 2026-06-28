import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from adk_agent import run_adk_agent as run_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str

@app.get("/")
def home():
    return {"status": "TechNova Club AI Agent Running!"}

@app.post("/ask")
def ask_agent(data: Question):
    try:
        answer = run_agent(data.question)
        return {
            "success": True,
            "question": data.question,
            "answer": answer
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/members")
def get_members():
    import json
    with open("../data/members.json", "r") as f:
        data = json.load(f)
    return data

@app.get("/stats")
def get_stats():
    import json
    with open("../data/members.json", "r") as f:
        members_data = json.load(f)
    with open("../data/events.json", "r") as f:
        events_data = json.load(f)
    with open("../data/achievements.json", "r") as f:
        achievements_data = json.load(f)

    members = members_data["members"]

    return {
        "total_members": len(members),
        "active_members": len([m for m in members if m["status"] == "active"]),
        "inactive_members": len([m for m in members if m["status"] == "inactive"]),
        "total_events": len(events_data["events"]),
        "total_achievements": len(achievements_data["achievements"]),
        "average_attendance": round(
            sum(m["attendance_percentage"] for m in members) / len(members), 1
        )
    }