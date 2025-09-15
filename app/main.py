from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="ChatBot",
    description="API de Perguntas & Respostas usando FastAPI e LangChain.",
    version="1.0.0",
)

app.include_router(chat_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
