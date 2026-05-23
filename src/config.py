import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PRODUCTION: bool = os.getenv("PRODUCTION", "false").strip().lower() == "true"
MOCK_ML: bool = os.getenv("MOCK_ML", "true").strip().lower() == "true"

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

if PRODUCTION:
    LLM_PROVIDER = "anthropic"
    LLM_MODEL = "claude-sonnet-4-6"
else:
    LLM_PROVIDER = "groq"
    LLM_MODEL = "llama-3.3-70b-versatile"

DNABERT_MODEL = "zhihan1996/DNABERT-2-117M"
MAX_SEQ_LENGTH = 512

BASE_DIR = Path(__file__).parent.parent
MODEL_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

for _dir in [MODEL_DIR, RESULTS_DIR / "metrics", RESULTS_DIR / "reports"]:
    _dir.mkdir(parents=True, exist_ok=True)

TRAIN_SIZE: int = int(os.getenv("TRAIN_SIZE", "20000"))
TEST_SIZE: int = int(os.getenv("TEST_SIZE", "5000"))
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "16"))
EPOCHS: int = int(os.getenv("EPOCHS", "5"))
LR: float = float(os.getenv("LR", "2e-5"))

API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
