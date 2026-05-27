from dotenv import load_dotenv
import os

# Load variables from .env into environment
load_dotenv()

# LangSmith / LangChain tracing
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "invoiceguard-ai-dev")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# New LangSmith variable names
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", LANGCHAIN_PROJECT)
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", LANGCHAIN_API_KEY)
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# OpenAI fallback
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://xinyanxie@localhost:28822/invoiceguard")

# Push values back into os.environ so LangChain/LangSmith libraries can read them
os.environ["LANGCHAIN_TRACING_V2"] = LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT

if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY

os.environ["LANGSMITH_TRACING"] = LANGSMITH_TRACING
os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT

if LANGSMITH_API_KEY:
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if POSTGRES_URL:
    os.environ["POSTGRES_URL"] = POSTGRES_URL
