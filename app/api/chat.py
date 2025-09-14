from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.qa import QAService

router = APIRouter()
qa_service = QAService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    answer, latency_ms = qa_service.get_answer_with_history(request.message, request.session_id)
    return ChatResponse(answer=answer, latency_ms=latency_ms)
