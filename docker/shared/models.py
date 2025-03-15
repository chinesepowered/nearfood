from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class Event(BaseModel):
    name: str
    url: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    food_description: Optional[str] = None
    initial_llm_response: Optional[str] = None
    final_llm_response: Optional[str] = None
    likelihood: Optional[str] = None

class EventSummary(BaseModel):
    events: List[Event]
    summary: Optional[str] = None
    processed_at: Optional[datetime] = None
    
class Message(BaseModel):
    content: str
    role: str  # "user" or "assistant"
    timestamp: Optional[datetime] = None

class Conversation(BaseModel):
    messages: List[Message] = []
    
class QueryResponse(BaseModel):
    status: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None