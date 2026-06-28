import json
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError(
        "QDRANT_URL and QDRANT_API_KEY must be set in .env (Qdrant Cloud credentials)."
    )

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

with open("../data/members.json", "r") as f:
    members_data = json.load(f)

with open("../data/events.json", "r") as f:
    events_data = json.load(f)

with open("../data/achievements.json", "r") as f:
    achievements_data = json.load(f)

def setup_qdrant():
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    
    if "club_members" not in names:
        client.create_collection(
            collection_name="club_members",
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        
        points = []
        for member in members_data["members"]:
            text = f"""
            {member['name']} is {member['role']}
            in {member['department']} department,
            year {member['year']}.
            Skills: {', '.join(member['skills'])}.
            Achievements: {', '.join(member['achievements'])}.
            Attendance: {member['attendance_percentage']}%.
            Status: {member['status']}.
            Performance score: {member['performance_score']}.
            """
            vector = model.encode(text).tolist()
            points.append(PointStruct(
                id=member['id'],
                vector=vector,
                payload=member
            ))
        
        client.upsert(
            collection_name="club_members",
            points=points
        )
    
    return client

qdrant = setup_qdrant()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Member Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def search_members(query: str) -> str:
    """Search members using semantic search"""
    
    query_vector = model.encode(query).tolist()
    
    results = qdrant.query_points(
        collection_name="club_members",
        query=query_vector,
        limit=5
    ).points
    
    if not results:
        return "No members found."
    
    members_found = []
    for r in results:
        p = r.payload
        members_found.append({
            "name": p["name"],
            "role": p["role"],
            "department": p["department"],
            "year": p["year"],
            "skills": p["skills"],
            "achievements": p["achievements"],
            "attendance": p["attendance_percentage"],
            "events_attended": p["events_attended"],
            "events_organized": p["events_organized"],
            "status": p["status"],
            "performance_score": p["performance_score"]
        })
    
    return json.dumps(members_found, indent=2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Performance Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def analyze_performance(filter_type: str = "all") -> str:
    """Analyze member performance"""
    
    members = members_data["members"]
    
    if filter_type == "top":
        filtered = sorted(
            members,
            key=lambda x: x["performance_score"],
            reverse=True
        )[:5]
    elif filter_type == "inactive":
        filtered = [
            m for m in members
            if m["status"] == "inactive"
        ]
    elif filter_type == "active":
        filtered = [
            m for m in members
            if m["status"] == "active"
        ]
    else:
        filtered = members

    total = len(members)
    active = len([m for m in members if m["status"] == "active"])
    inactive = len([m for m in members if m["status"] == "inactive"])
    avg_attendance = sum(
        m["attendance_percentage"] for m in members
    ) / total

    analysis = {
        "summary": {
            "total_members": total,
            "active_members": active,
            "inactive_members": inactive,
            "average_attendance": round(avg_attendance, 1)
        },
        "members": [
            {
                "name": m["name"],
                "role": m["role"],
                "attendance": m["attendance_percentage"],
                "performance_score": m["performance_score"],
                "events_organized": len(m["events_organized"]),
                "achievements_count": len(m["achievements"]),
                "status": m["status"]
            }
            for m in filtered
        ]
    }
    
    return json.dumps(analysis, indent=2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Recommendations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_recommendations(recommendation_type: str) -> str:
    """Get smart recommendations"""
    
    members = members_data["members"]
    events = events_data["events"]
    achievements = achievements_data["achievements"]

    if recommendation_type == "next_president":
        candidates = sorted(
            [m for m in members if m["status"] == "active"],
            key=lambda x: (
                x["performance_score"] * 0.4 +
                x["attendance_percentage"] * 0.3 +
                len(x["events_organized"]) * 10 * 0.3
            ),
            reverse=True
        )[:3]
        
        result = {
            "type": "Next President Recommendation",
            "top_candidates": [
                {
                    "name": c["name"],
                    "role": c["role"],
                    "performance_score": c["performance_score"],
                    "attendance": c["attendance_percentage"],
                    "events_organized": len(c["events_organized"]),
                    "achievements": c["achievements"],
                    "reason": f"High performance score of {c['performance_score']}, {c['attendance_percentage']}% attendance"
                }
                for c in candidates
            ]
        }

    elif recommendation_type == "engage_inactive":
        inactive = [
            m for m in members
            if m["status"] == "inactive"
        ]
        result = {
            "type": "Inactive Member Engagement",
            "inactive_members": [
                {
                    "name": m["name"],
                    "department": m["department"],
                    "attendance": m["attendance_percentage"],
                    "skills": m["skills"]
                }
                for m in inactive
            ],
            "strategies": [
                "Personal one-on-one meeting பண்ணுங்க",
                "அவங்க skills-க்கு match ஆன events assign பண்ணுங்க",
                "Buddy system — active member pair பண்ணுங்க",
                "Monthly check-in call பண்ணுங்க",
                "Small responsibilities கொடுங்க — confidence build ஆகும்"
            ]
        }

    elif recommendation_type == "best_performer":
        top = sorted(
            members,
            key=lambda x: x["performance_score"],
            reverse=True
        )[:3]
        result = {
            "type": "Best Performers",
            "top_performers": [
                {
                    "rank": i + 1,
                    "name": m["name"],
                    "role": m["role"],
                    "performance_score": m["performance_score"],
                    "attendance": m["attendance_percentage"],
                    "achievements": m["achievements"]
                }
                for i, m in enumerate(top)
            ]
        }

    elif recommendation_type == "club_summary":
        result = {
            "type": "Club Summary",
            "club_name": members_data["club"]["name"],
            "total_members": len(members),
            "active_members": len([m for m in members if m["status"] == "active"]),
            "inactive_members": len([m for m in members if m["status"] == "inactive"]),
            "total_events": len(events),
            "total_achievements": len(achievements),
            "average_attendance": round(
                sum(m["attendance_percentage"] for m in members) / len(members), 1
            ),
            "top_performer": max(members, key=lambda x: x["performance_score"])["name"],
            "most_events_organized": max(members, key=lambda x: len(x["events_organized"]))["name"]
        }
    else:
        result = {"error": "Unknown recommendation type"}

    return json.dumps(result, indent=2)


# Test பண்ணு
if __name__ == "__main__":
    print("Testing Tool 1 - Search Members:")
    print(search_members("who is the president"))
    
    print("\nTesting Tool 2 - Top Performers:")
    print(analyze_performance("top"))
    
    print("\nTesting Tool 3 - Best Performer Recommendation:")
    print(get_recommendations("best_performer"))