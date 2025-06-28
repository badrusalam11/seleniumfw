# File: core/config.py
import os
from dotenv import load_dotenv
import glob

class Config:
    def __init__(self, env_file=".env", properties_dir="settings"):
        # Load all .properties files in settings/ directory
        self.properties = {}
        if os.path.isdir(properties_dir):
            for filepath in glob.glob(os.path.join(properties_dir, "*.properties")):
                self._load_properties_file(filepath)
        # Load .env first
        load_dotenv(env_file)

    def _load_properties_file(self, filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                self.properties[key.strip()] = val.strip()

    def get(self, key, default=None):
        # 1) Try environment variables (.env takes precedence)
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        # 2) Fallback to properties file
        return self.properties.get(key, default)

    def get_list(self, key, default=None, sep=";"):
        raw = self.get(key, "")
        if not raw:
            return default or []
        return [item.strip() for item in raw.split(sep) if item.strip()]
