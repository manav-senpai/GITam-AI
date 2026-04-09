"""
LLM Client - Handles Groq (primary) and Ollama (fallback) for AI inference.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_llm_client():
    """Returns a configured OpenAI-compatible client for Groq."""
    return OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )


def get_ollama_client():
    """Returns a configured OpenAI-compatible client for local Ollama."""
    return OpenAI(
        api_key="ollama",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1",
    )


def ask_llm(prompt: str, system_prompt: str = "You are a helpful AI assistant.", max_tokens: int = 2048) -> str:
    """
    Ask the LLM a question. Tries Groq first, falls back to Ollama.
    """
    # Try Groq first
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[LLM] Groq failed: {e}. Falling back to Ollama...")

    # Fallback to Ollama
    try:
        client = get_ollama_client()
        response = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[LLM] Ollama also failed: {e}")
        return f"[LLM Error] Both Groq and Ollama failed. Last error: {e}"
