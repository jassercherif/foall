from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# ----------------------
# Load environment variables (optional)
# ----------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "fastapi_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "application_logs")

# ----------------------
# MongoDB client
# ----------------------
client = MongoClient(MONGO_URI, tls=True)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ----------------------
# FastAPI app
# ----------------------
app = FastAPI()

# Helper to prepare document for MongoDB
def prepare_doc(payload: dict) -> dict:
    """
    Normalize the payload and add metadata before storing.
    """
    doc = dict(payload)  # copy the payload
    doc["_received_at"] = datetime.utcnow()
    return doc

# Helper to make document JSON serializable
def serialize_doc(doc: dict) -> dict:
    """
    Convert MongoDB types (datetime, ObjectId) to JSON-friendly types.
    """
    serialized = dict(doc)
    # Convert datetime to ISO string
    if "_received_at" in serialized:
        serialized["_received_at"] = serialized["_received_at"].isoformat() + "Z"
    return serialized

@app.post("/application-log")
async def receive_log(request: Request):
    """
    Receive ApplicationLog from Salesforce and store it in MongoDB.
    """
    data = None

    # 1️⃣ Try JSON body
    try:
        data = await request.json()
    except Exception as e_json:
        print("No valid JSON:", repr(e_json))

    # 2️⃣ Try form data if JSON is empty
    if not data:
        try:
            form = await request.form()
            if form:
                data = dict(form)
        except Exception as e_form:
            print("No form data:", repr(e_form))

    # 3️⃣ Fallback to query params
    if not data:
        data = dict(request.query_params)

    # 4️⃣ If still empty, return error
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty request. Send JSON, form data, or query params."
        )

    # 5️⃣ Store in MongoDB
    doc = prepare_doc(data)
    try:
        inserted = collection.insert_one(doc)
        inserted_id = inserted.inserted_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB insert failed: {e}")

    print(f"Stored ApplicationLog with ID: {inserted_id}")

    # 6️⃣ Serialize doc for JSON response
    response_doc = serialize_doc(doc)

    return {"ok": True, "inserted_id": str(inserted_id), "stored_data": response_doc}
