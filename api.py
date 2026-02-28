import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.llm import LLMChain

# Load env variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI(title="Prospektüs AI API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global resources
prospektus_db = None
llm = None
ilac_memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')
ilac_chain = None

# Custom Prompts
condense_question_template = "Sohbet geçmişi ve takip sorusu verildiğinde, onu tam bir soruya dönüştür.\n\nChat History:\n{chat_history}\nFollow Up Input: {question}\nStandalone question:"
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_question_template)

@app.on_event("startup")
async def startup_event():
    global prospektus_db, llm, ilac_chain
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in env.")
        return
    
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    
    try:
        prospektus_db = Chroma(persist_directory='prospektus_db', embedding_function=embeddings)
        print("Prospektüs DB loaded successfully.")
    except Exception as e:
        print(f"Error loading Prospektüs DB: {e}")

    try:
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key=api_key)
        
        question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
        doc_chain = load_qa_chain(llm, chain_type="stuff")

        ilac_chain = ConversationalRetrievalChain(
            retriever=prospektus_db.as_retriever(search_kwargs={"k": 4}),
            combine_docs_chain=doc_chain,
            question_generator=question_generator,
            memory=ilac_memory,
            rephrase_question=False,
            return_source_documents=True
        )
        print("LangChain pipeline initialized successfully.")
    except Exception as e:
        print(f"Error initializing LangChain: {e}")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []

import traceback
import sqlite3
import hashlib
import binascii

# DB Init
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Hash utility
def hash_password(password: str) -> str:
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password: str, provided_password: str) -> bool:
    salt = stored_password[:64]
    stored_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_hash

init_db()

class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    is_admin: bool = False

@app.post("/api/register", response_model=AuthResponse)
async def register(request: AuthRequest):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (request.username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Otomatik ledurullah admin kaydı kuralı vs. gerekebilir ama direkt insert
    is_admin = 1 if request.username == "ledurullah" else 0
    hashed_pw = hash_password(request.password)
    c.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", 
              (request.username, hashed_pw, is_admin))
    conn.commit()
    conn.close()
    return AuthResponse(success=True, message="Registration successful", is_admin=bool(is_admin))

@app.post("/api/login", response_model=AuthResponse)
async def login(request: AuthRequest):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, is_admin FROM users WHERE username=?", (request.username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
        
    stored_password, is_admin = user
    if not verify_password(stored_password, request.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
        
    return AuthResponse(success=True, message="Login successful", is_admin=bool(is_admin))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not ilac_chain:
        raise HTTPException(status_code=500, detail="AI pipeline is not initialized properly.")
    
    try:
        print(f"User message received: {request.message}")
        response = ilac_chain.invoke({"question": request.message})
        
        # Extract unique sources from metadata while preserving relevance order
        sources = []
        seen = set()
        if 'source_documents' in response:
            for doc in response['source_documents']:
                src_raw = doc.metadata.get('source', 'Unknown')
                if src_raw != 'Unknown':
                    # Sadece dosya ismini al ve uzantıyı temizle (.txt, .pdf vs)
                    src_clean = os.path.basename(src_raw).rsplit('.', 1)[0]
                    # Listede yoksa ekle (böylece en alakalı olan ilk sırada kalır)
                    if src_clean not in seen:
                        seen.add(src_clean)
                        sources.append(src_clean)
            
        print(f"Reply generated with {len(sources)} sources.")
        return ChatResponse(answer=response['answer'], sources=sources)
    except Exception as e:
        print("ERROR IN CHAT ENDPOINT:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
