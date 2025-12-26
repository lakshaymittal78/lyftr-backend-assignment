import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./messages.db")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")
    
    def validate(self):
        """Validate required settings"""
        if not self.WEBHOOK_SECRET:
            raise ValueError("WEBHOOK_SECRET environment variable must be set")


settings = Settings()