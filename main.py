from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "fastapi_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "application_logs")

client = MongoClient(MONGO_URI, tls=True)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI()

# ----------------------
# Helpers
# ----------------------
def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB types to JSON-serializable format."""
    serialized = dict(doc)
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    if "_received_at" in serialized:
        serialized["_received_at"] = serialized["_received_at"].isoformat() + "Z"
    return serialized

def prepare_doc(payload: dict) -> dict:
    doc = dict(payload)
    doc["_received_at"] = datetime.utcnow()
    return doc

# ----------------------
# POST endpoint
# ----------------------
@app.post("/application-log")
async def receive_log(request: Request):
    data = None
    try:
        data = await request.json()
    except:
        try:
            form = await request.form()
            if form:
                data = dict(form)
        except:
            pass

    if not data:
        data = dict(request.query_params)

    if not data:
        raise HTTPException(status_code=400, detail="Empty request. Send JSON, form data, or query params.")

    doc = prepare_doc(data)
    try:
        inserted = collection.insert_one(doc)
        inserted_id = inserted.inserted_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB insert failed: {e}")

    return {"ok": True, "inserted_id": str(inserted_id), "stored_data": serialize_doc(doc)}

# ----------------------
# GET endpoint
# ----------------------
@app.get("/application-log")
async def get_logs(limit: int = 50):
    try:
        cursor = collection.find().sort("_received_at", -1).limit(limit)
        logs = [serialize_doc(doc) for doc in cursor]  # serialize each doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB query failed: {e}")

    return {"ok": True, "count": len(logs), "logs": logs}
