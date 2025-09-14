from dotenv import load_dotenv
import time
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

class QAService:
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Atue como um assistente de IA que responde perguntas"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        self.chain = self.prompt | model
        
        self.llm_chain = (
            RunnablePassthrough.assign(
                history=lambda input_dict: self.memory_window(input_dict["history"])
            )
            |self.prompt
            |model
            |StrOutputParser()
        )
        
        self.conv_chain = RunnableWithMessageHistory(
            self.llm_chain,
            self.get_session_history_db,
            input_messages_key="question",
            history_messages_key="history"
        )
        
        
    def get_session_history_db(self, session_id):
        return SQLChatMessageHistory(session_id, connection="sqlite:///memory.db")
    
    def memory_window(self, messages, k=10):
        if not isinstance(messages, list):
            return []
        return messages[-(k+1):]
    
    
    def get_answer_with_history(self, question: str, session_id: str) -> tuple[str, int]:
        start_time = time.perf_counter()
        response = self.conv_chain.invoke(
            {"question": question},
            config={"configurable": {"session_id" : session_id}}
        )
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 100)
        
        if isinstance(response, (list, dict)):
            content_str = str(response)
        else:
            content_str = response
        return content_str, latency_ms