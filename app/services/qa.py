from dotenv import load_dotenv
import time
from langchain.llms import FakeListLLM
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o"
)

class QAService:
    def __init__(self):
        self.prompt = ChatPromptTemplate([(
            "user", "Você é um assistente que responde perguntas: {question}"
        )])
        self.chain = self.prompt | model

    def get_answer(self, question: str) -> tuple[str, int]:
        start_time = time.perf_counter()
        response = self.chain.invoke({"question": question})
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)
        # Ensure response.content is a string, as per the type hint
        if isinstance(response.content, (list, dict)):
            # If it's a list or dict, convert it to a string representation
            content_str = str(response.content)
        else:
            content_str = response.content
        return content_str, latency_ms
