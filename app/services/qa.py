from dotenv import load_dotenv
import time
import os
from typing import List, Tuple

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

embeddings = OpenAIEmbeddings()

class QAService:
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Atue como um assistente de IA que responde perguntas. Use os trechos de contexto fornecidos para responder à pergunta. Se a pergunta não puder ser respondida com o contexto fornecido, diga 'Não consigo responder a esta pergunta com o contexto fornecido.'"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Contexto: {context}\nPergunta: {question}")
        ])
        
        self.llm_chain = (
            RunnablePassthrough.assign(
                history=lambda input_dict: self.memory_window(input_dict["history"])
            )
            | self.prompt
            | model
            | StrOutputParser()
        )
        
        self.conv_chain = RunnableWithMessageHistory(
            self.llm_chain,
            self.get_session_history_db,
            input_messages_key="question",
            history_messages_key="history"
        )
        
        self.vectorstores = {} # Stores FAISS vector stores per session_id

    def get_session_history_db(self, session_id):
        return SQLChatMessageHistory(session_id, connection="sqlite:///memory.db")
    
    def memory_window(self, messages, k=10):
        if not isinstance(messages, list):
            return []
        return messages[-(k+1):]
    
    def get_answer_with_history(self, question: str, session_id: str) -> tuple[str, int]:
        start_time = time.perf_counter()
        response = self.conv_chain.invoke(
            {"question": question, "context": ""}, # Empty context for regular chat
            config={"configurable": {"session_id" : session_id}}
        )
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 100)
        
        if isinstance(response, (list, dict)):
            content_str = str(response)
        else:
            content_str = response
        return content_str, latency_ms

    def upload_document(self, file_content: str, file_name: str, session_id: str):
        # Create a temporary file to load with TextLoader
        temp_file_path = f"/tmp/{session_id}_{file_name}"
        with open(temp_file_path, "w") as f:
            f.write(file_content)

        loader = TextLoader(temp_file_path)
        documents = loader.load()
        
        # Add metadata for source tracking
        for i, doc in enumerate(documents):
            doc.metadata = {"document_name": file_name, "page_number": i + 1}

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        vectorstore = FAISS.from_documents(splits, embeddings)
        self.vectorstores[session_id] = vectorstore
        
        os.remove(temp_file_path) # Clean up temporary file

    def ask_document(self, question: str, session_id: str) -> Tuple[str, List[dict], int]:
        start_time = time.perf_counter()
        
        if session_id not in self.vectorstores:
            return "Nenhum documento foi carregado para esta sessão.", [], 0

        vectorstore = self.vectorstores[session_id]
        retriever = vectorstore.as_retriever()
        
        docs = retriever.invoke(question)
        
        context = "\n\n".join([doc.page_content for doc in docs])
        
        response = self.conv_chain.invoke(
            {"question": question, "context": context},
            config={"configurable": {"session_id" : session_id}}
        )
        
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 100)

        sources = []
        for doc in docs:
            sources.append({
                "document_name": doc.metadata.get("document_name", "N/A"),
                "page_content": doc.page_content,
                "page_number": doc.metadata.get("page_number")
            })
        
        if isinstance(response, (list, dict)):
            content_str = str(response)
        else:
            content_str = response
            
        return content_str, sources, latency_ms
