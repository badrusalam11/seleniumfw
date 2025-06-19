import os
from dotenv import load_dotenv

class Config:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)
        self.environment = os.getenv("ENV", "dev")

    def get(self, key, default=None):
        return os.getenv(key, default)
