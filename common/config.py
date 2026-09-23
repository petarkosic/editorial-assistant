import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
DATA_DIR = REPO_ROOT / "data"
RUNS_DIR = DATA_DIR / "runs"

MODEL_SCOUT = os.getenv("SCOUT_MODEL", "gemini-3.5-flash-lite")
MODEL_RESEARCH = os.getenv("RESEARCH_MODEL", "gemini-3.5-flash-lite")
MODEL_SYNTHESIS = os.getenv("SYNTHESIS_MODEL", "gemini-3.5-flash-lite")
MODEL_JUDGE = os.getenv("JUDGE_MODEL", "gemini-3.5-flash-lite")

RESEARCH_CONCURRENCY = int(os.getenv("RESEARCH_CONCURRENCY", "3"))
RESEARCH_MAX_TOOL_CALLS = int(os.getenv("RESEARCH_MAX_TOOL_CALLS", "6"))

FETCH_TIMEOUT_SECONDS = 10
FETCH_CHAR_CAP = 6000
FETCH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
