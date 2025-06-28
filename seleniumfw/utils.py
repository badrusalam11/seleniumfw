# seleniumfw/utils.py

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader


def load_env(env_path: str = ".env") -> None:
    """Load environment variables from .env."""
    load_dotenv(env_path)


def render_template(template_name: str, context: dict, dest: Path, base_template_dir: Path):
    env = Environment(loader=FileSystemLoader(str(base_template_dir)))
    tpl = env.get_template(template_name)
    content = tpl.render(**context)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)



class Logger:
    @staticmethod
    def get_logger(name: str = __name__) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
