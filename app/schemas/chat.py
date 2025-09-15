from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    latency_ms: Optional[int] = None

class Source(BaseModel):
    document_name: str
    page_content: str
    page_number: Optional[int] = None

class DocumentUploadRequest(BaseModel):
    session_id: str

class AskRequest(BaseModel):
    question: str
    session_id: str

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    latency_ms: Optional[int] = None
