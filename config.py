"""
Configuration file for the banking agent system
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Verify API key is set
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Please set it in your .env file or environment variables."
    )

# File paths
DATA_DIR = "data"
CUSTOMERS_FILE = os.path.join(DATA_DIR, "clientes.csv")
SCORE_LIMIT_FILE = os.path.join(DATA_DIR, "score_limite.csv")
REQUESTS_FILE = os.path.join(DATA_DIR, "solicitacoes_aumento_limite.csv")

# Agent configuration
MAX_AUTH_ATTEMPTS = 3

# LLM Settings
LLM_TEMPERATURE = 0
LLM_MAX_TOKENS = 1000