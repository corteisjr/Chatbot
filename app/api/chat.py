from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse, AskResponse, Source
from app.services.qa import QAService

router = APIRouter()
qa_service = QAService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    answer, latency_ms = qa_service.get_answer_with_history(request.message, request.session_id)
    return ChatResponse(answer=answer, latency_ms=latency_ms)

@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    question: str,
    session_id: str,
    file: UploadFile = File(None)
):
    if file:
        if file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is missing."
            )
        if not file.filename.endswith((".txt", ".md")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt and .md files are allowed."
            )
        
        file_content = await file.read()
        file_content_str = file_content.decode("utf-8")
        
        qa_service.upload_document(file_content_str, file.filename, session_id)
        
        # After uploading, answer the question
        answer, raw_sources, latency_ms = qa_service.ask_document(question, session_id)
        sources = [Source(**s) for s in raw_sources]
        return AskResponse(answer=answer, sources=sources, latency_ms=latency_ms)
    else:
        # If no file is uploaded, just answer the question using existing indexed documents
        answer, raw_sources, latency_ms = qa_service.ask_document(question, session_id)
        sources = [Source(**s) for s in raw_sources]
        return AskResponse(answer=answer, sources=sources, latency_ms=latency_ms)
