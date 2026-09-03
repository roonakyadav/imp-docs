import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)
logger = logging.getLogger('browser-agent')

# Local Inference Config (Ollama)
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Agent Runtime Config
MAX_STEPS = int(os.getenv("MAX_STEPS", "20")) # Reduced for local model stability
RETRIES = int(os.getenv("RETRIES", "3"))
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

# Browser Settings
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

def validate_config():
    """Validates that essential configuration is present."""
    # Since we are local now, we just check if Ollama settings are present
    if not OLLAMA_HOST:
        logger.error("OLLAMA_HOST is missing.")
        return False
    return True
