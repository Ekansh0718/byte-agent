# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Optional server-side fallbacks (used only if client didn't provide keys)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MURF_API_KEY = os.getenv("MURF_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
