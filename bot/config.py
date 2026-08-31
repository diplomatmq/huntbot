import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
BOT_OWNER_ID = 793216884

# Game constants
MAX_ENERGY = 100
ENERGY_REGEN_PASSIVE = 1  # per 5 minutes
ENERGY_REGEN_FOOD = 20  # per portion
HUNT_COOLDOWN = 600  # 10 minutes in seconds
LOCATION_UNLOCK_THRESHOLD = 80  # percent
BOSS_UNLOCK_THRESHOLD = 70  # percent
MAX_ACCURACY = 95  # percent
BASE_ACCURACY = 70  # percent
