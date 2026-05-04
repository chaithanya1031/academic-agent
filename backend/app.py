#app.py
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.agents import initialize_agent, AgentType
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import re
import os
from dotenv import load_dotenv
import os

import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

google_model = genai.GenerativeModel("models/gemini-2.0-flash")

load_dotenv()
# ---------- LLM ----------
model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    max_tokens=500,
    timeout=30,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# ---------- TOOLS ----------
@tool
def mathematical_calculations(expression: str) -> str:
    """Perform mathematical calculations like addition, subtraction, multiplication, division."""
    clean_expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
    try:
        result = eval(clean_expression, {"__builtins__": None}, {})
        return str(result)
    except:
        return "Error"

@tool
def unit_converter(query: str) -> str:
    """Convert units like meters to kilometers or hours to minutes."""
    match = re.search(r'([\d.]+)\s*(\w+)\s*to\s*(\w+)', query.lower())
    if not match:
        return "Invalid format"

    value, u1, u2 = float(match.group(1)), match.group(2), match.group(3)

    if u1 == "meters" and u2 == "kilometers":
        return str(value * 0.001)
    if u1 == "hours" and u2 == "minutes":
        return str(value * 60)

    return "Not supported"

@tool
def conceptual_explainer(query: str) -> str:
    """Explain concepts clearly in detail and add simple real world example to it for better understanding."""
    return f"Explain: {query}"

tools = [mathematical_calculations, unit_converter, conceptual_explainer]

agent = initialize_agent(
    tools,
    model,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    agent_kwargs={
        "prefix": "You are a helpful assistant. answer directly.  Do NOT show reasoning."
    }
)
def run_groq_agent(query: str):
    return agent.run(query)


def run_google_llm(query: str):
    response = google_model.generate_content(query)
    return response.text
# ---------- API ----------
app = FastAPI()

class Query(BaseModel):
    input: str

@app.post("/ask")
def ask(q: Query):
    # 1️⃣ Try Groq first
    try:
        response = run_groq_agent(q.input)
        return {
            "response": response,
            "provider": "groq"
        }

    except Exception as groq_error:
        # 🔒 Visible only in logs
        print("Groq failed:", groq_error)

        # 2️⃣ Fallback to Google
        try:
            response = run_google_llm(q.input)
            return {
                "response": response,
                "provider": "google"
            }

        except Exception as google_error:
            print("Google failed:", google_error)

            # 3️⃣ Retry Groq
            try:
                response = run_groq_agent(q.input)
                return {
                    "response": response,
                    "provider": "groq-retry"
                }

            except Exception as final_error:
                print("Final failure:", final_error)

                # 🔒 Clean user-safe message
                return {
                    "response": "Sorry, the system is temporarily unavailable. Please try again."
                }
@app.get("/")
def root():
    return {"status": "running", "version": "v1"}
