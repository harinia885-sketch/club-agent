import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Embedding model load
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Qdrant client (in-memory — no server needed!)
client = QdrantClient(":memory:")

# Collection create
client.create_collection(
    collection_name="club_members",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    )
)

# Members data load
with open("../data/members.json", "r") as f:
    data = json.load(f)

members = data["members"]

# Each member-ஐ text-ஆ convert பண்ணு
print("Creating embeddings...")
points = []

for member in members:
    # Member info text-ஆ combine பண்ணு
    text = f"""
    {member['name']} is {member['role']} 
    in {member['department']} department, 
    year {member['year']}.
    Skills: {', '.join(member['skills'])}.
    Achievements: {', '.join(member['achievements'])}.
    Attendance: {member['attendance_percentage']}%.
    Events attended: {', '.join(member['events_attended'])}.
    Status: {member['status']}.
    Performance score: {member['performance_score']}.
    """

    # Text → Vector
    vector = model.encode(text).tolist()

    # Point create
    points.append(PointStruct(
        id=member['id'],
        vector=vector,
        payload={
            "name": member['name'],
            "role": member['role'],
            "department": member['department'],
            "year": member['year'],
            "skills": member['skills'],
            "achievements": member['achievements'],
            "attendance": member['attendance_percentage'],
            "events_attended": member['events_attended'],
            "events_organized": member['events_organized'],
            "status": member['status'],
            "performance_score": member['performance_score'],
            "text": text
        }
    ))

# Qdrant-ல upload பண்ணு
client.upsert(
    collection_name="club_members",
    points=points
)

print(f"Uploaded {len(points)} members to Qdrant!")

# Test search பண்ணு
print("\nTesting semantic search...")
query = "who is the best leader?"
query_vector = model.encode(query).tolist()

results = client.query_points(
    collection_name="club_members",
    query=query_vector,
    limit=3
).points

print("\nTop 3 results for 'who is the best leader?':")
for r in results:
    print(f"  → {r.payload['name']} ({r.payload['role']}) - Score: {r.score:.2f}")

print("\nQdrant setup complete!")