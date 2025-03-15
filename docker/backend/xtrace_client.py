import requests
import os
import json
import uuid
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# xTrace API configuration
XTRACE_API_URL = os.environ.get("XTRACE_API_URL", "https://api.xtrace.ai/v1")
XTRACE_API_KEY = os.environ.get("XTRACE_API_KEY")

class XTraceError(Exception):
    """Exception raised for xTrace API errors"""
    pass

def get_headers() -> Dict[str, str]:
    """Get HTTP headers for xTrace API requests"""
    if not XTRACE_API_KEY:
        raise XTraceError("XTRACE_API_KEY environment variable not set")
    
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XTRACE_API_KEY}"
    }

def upload_data_to_xtrace(data: Any) -> Dict[str, Any]:
    """Upload processed event data to xTrace"""
    try:
        # Prepare data for xTrace
        trace_id = str(uuid.uuid4())
        
        upload_data = {
            "trace_id": trace_id,
            "metadata": {
                "source": "calendar_processor",
                "version": "1.0",
                "processed_at": datetime.now().isoformat()
            },
            "content": data
        }
        
        # Upload to xTrace
        response = requests.post(
            f"{XTRACE_API_URL}/traces",
            headers=get_headers(),
            json=upload_data
        )
        
        response.raise_for_status()
        
        print(f"Data uploaded to xTrace with trace_id: {trace_id}")
        return {
            "status": "success",
            "trace_id": trace_id,
            "response": response.json()
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"xTrace API error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" - {e.response.text}"
        
        print(error_msg)
        raise XTraceError(error_msg)

def query_xtrace(question: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Query xTrace with a question"""
    try:
        # Convert chat history to xTrace format if provided
        formatted_history = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get("is_user", False) else "assistant"
                content = msg.get("message", "")
                formatted_history.append({"role": role, "content": content})
        
        # Prepare query data
        query_data = {
            "query": question,
            "chat_history": formatted_history
        }
        
        # Send query to xTrace
        response = requests.post(
            f"{XTRACE_API_URL}/queries",
            headers=get_headers(),
            json=query_data
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "status": "success",
            "answer": result.get("answer", "No answer provided"),
            "sources": result.get("sources", []),
            "metadata": result.get("metadata", {})
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"xTrace query error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" - {e.response.text}"
        
        print(error_msg)
        raise XTraceError(error_msg)