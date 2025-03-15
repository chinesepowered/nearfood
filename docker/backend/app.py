from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime

from ical_processor import process_ical_data, get_event_summaries
from xtrace_client import upload_data_to_xtrace, query_xtrace
from inference_provider import get_inference_provider

app = FastAPI(title="Food Event Chatbot API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage paths
DATA_DIR = os.environ.get("DATA_DIR", "./data")
ICAL_DATA_PATH = os.path.join(DATA_DIR, "ical_data.json")
SUMMARY_PATH = os.path.join(DATA_DIR, "event_summary.json")
PROCESSED_FLAG_PATH = os.path.join(DATA_DIR, "processed_flag.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Models
class ChatMessage(BaseModel):
    message: str
    is_user: bool = True

class ChatHistory(BaseModel):
    messages: List[ChatMessage] = []

class ProcessRequest(BaseModel):
    ical_url: str
    force_reprocess: bool = False

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[ChatHistory] = None

# Check if initial processing has been done
def check_processed():
    if not os.path.exists(PROCESSED_FLAG_PATH):
        return False
    
    with open(PROCESSED_FLAG_PATH, "r") as f:
        data = json.load(f)
    
    return data.get("processed", False)

# Set processed flag
def set_processed_flag(processed=True):
    with open(PROCESSED_FLAG_PATH, "w") as f:
        json.dump({"processed": processed, "timestamp": datetime.now().isoformat()}, f)

# Routes
@app.get("/")
async def root():
    return {"status": "online", "service": "Food Event Chatbot API"}

@app.post("/process")
async def process_calendar(
    request: ProcessRequest, 
    background_tasks: BackgroundTasks
):
    """Process iCal data, analyze for free food events, and upload to xTrace"""
    
    # Check if already processed and not forcing reprocess
    if check_processed() and not request.force_reprocess:
        return {
            "status": "skipped", 
            "message": "Data already processed. Use force_reprocess=true to reprocess."
        }
    
    # Get inference provider
    inference_provider = get_inference_provider()
    if not inference_provider:
        raise HTTPException(
            status_code=500, 
            detail="Failed to initialize inference provider. Check API key."
        )
    
    try:
        # Process in background to avoid timeout
        background_tasks.add_task(
            process_ical_data,
            request.ical_url,
            ICAL_DATA_PATH,
            SUMMARY_PATH,
            inference_provider
        )
        
        # Upload processed data to xTrace in background
        def process_and_upload():
            # Wait for processing to complete
            event_summaries = get_event_summaries(SUMMARY_PATH)
            if event_summaries:
                # Upload to xTrace
                upload_result = upload_data_to_xtrace(event_summaries)
                # Set processed flag
                set_processed_flag(True)
                return upload_result
            return {"status": "error", "message": "No event summaries found"}
            
        background_tasks.add_task(process_and_upload)
        
        return {
            "status": "processing",
            "message": "Processing calendar data and uploading to xTrace in background"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/query")
async def query(request: QueryRequest):
    """Query xTrace with a question about food events"""
    
    # Check if data has been processed first
    if not check_processed():
        raise HTTPException(
            status_code=400, 
            detail="Calendar data has not been processed yet. Run /process endpoint first."
        )
    
    try:
        # Send query to xTrace
        response = query_xtrace(request.question, 
                              request.chat_history.messages if request.chat_history else [])
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/status")
async def status():
    """Check if calendar data has been processed"""
    processed = check_processed()
    
    result = {
        "processed": processed,
        "ical_data_exists": os.path.exists(ICAL_DATA_PATH),
        "summary_data_exists": os.path.exists(SUMMARY_PATH)
    }
    
    if processed and os.path.exists(PROCESSED_FLAG_PATH):
        with open(PROCESSED_FLAG_PATH, "r") as f:
            flag_data = json.load(f)
            result["processed_timestamp"] = flag_data.get("timestamp")
    
    return result

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)