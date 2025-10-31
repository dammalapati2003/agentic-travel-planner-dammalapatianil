from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

@dataclass
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    opentripmap_api_key: str = os.getenv("OPENTRIPMAP_API_KEY", "")
    app_tz: str = os.getenv("APP_TIMEZONE", "Asia/Kolkata")

settings = Settings()

# ✅ Normalize timezone 
if settings.app_tz == "Asia/Kolkata":
    try:
        import zoneinfo
        _ = zoneinfo.ZoneInfo("Asia/Kolkata")
    except Exception:
        # Windows fallback
        settings.app_tz = "Asia/Calcutta"
