# services/llm.py
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# optional imports - wrap to allow running if client not installed
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

# optional serpapi
try:
    from serpapi import GoogleSearch
    SERP_AVAILABLE = True
except Exception:
    SERP_AVAILABLE = False

SYSTEM_INSTRUCTIONS = """
You are BYTE (Machine-based Assistant for Research, Voice, and Interactive Services).
Be concise, slightly witty, and helpful. Keep replies short unless user requests long details.
"""

def should_search_web(user_query: str, api_key: str) -> bool:
    if not GENAI_AVAILABLE or not api_key:
        return False
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Answer with 'yes' or 'no' only. Does the following query require a web search to answer accurately? Query: {user_query}"
        resp = model.generate_content(prompt)
        return resp.text.strip().lower().startswith("yes")
    except Exception as e:
        logger.exception("should_search_web failed")
        return False

def get_llm_response(user_query: str, history: List[Dict[str, Any]], api_key: str) -> Tuple[str, List[Dict[str, Any]]]:
    # fallback if gemini not installed
    if not GENAI_AVAILABLE or not api_key:
        fallback = f"I can't access Gemini here. Echo: {user_query}"
        return fallback, history
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_INSTRUCTIONS)
        chat = model.start_chat(history=history)
        resp = chat.send_message(user_query)
        return resp.text, chat.history
    except Exception as e:
        logger.exception("LLM request failed")
        return f"LLM error: {e}", history

def get_web_response(user_query: str, history: List[Dict[str, Any]], gemini_api_key: str, serp_api_key: str) -> Tuple[str, List[Dict[str, Any]]]:
    if not SERP_AVAILABLE or not serp_api_key:
        return "Web search not available (SerpAPI missing).", history
    try:
        params = {"q": user_query, "engine": "google", "api_key": serp_api_key}
        s = GoogleSearch(params)
        res = s.get_dict()
        snippets = []
        for r in res.get("organic_results", [])[:5]:
            snippets.append(r.get("snippet") or r.get("title") or "")
        context = "\n".join(snippets)
        prompt = f"Use the search results below to answer concisely. Query: {user_query}\n\nContext:\n{context}"
        return get_llm_response(prompt, history, gemini_api_key)
    except Exception as e:
        logger.exception("Web response failed")
        return f"Web search error: {e}", history
