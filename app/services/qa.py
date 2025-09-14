import time
from langchain.llms import FakeListLLM
from langchain.prompts import PromptTemplate

class QAService:
    def __init__(self):
        self.llm = FakeListLLM(responses=["A capital da França é Paris.", "A resposta é 42.", "Olá! Como posso ajudar?"])
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template="Você é um assistente de IA. Responda à seguinte pergunta: {question}"
        )
        self.chain = self.prompt | self.llm

    def get_answer(self, question: str) -> tuple[str, int]:
        start_time = time.perf_counter()
        response = self.chain.invoke({"question": question})
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)
        return response, latency_ms
