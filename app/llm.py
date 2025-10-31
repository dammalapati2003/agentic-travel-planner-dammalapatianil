from groq import Groq
from .config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY missing. Set it in .env")
        _client = Groq(api_key=settings.groq_api_key)
    return _client

def chat(messages, temperature=0.2, model=None):
    client = get_client()
    model = model or settings.llm_model
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type":"text"},
    )
    return resp.choices[0].message.content.strip()
