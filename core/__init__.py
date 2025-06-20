# core/__init__.py
import sys
from core.runner import Runner
from core.utils import Logger

def run():
    logger = Logger.get_logger()

    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <suite_file.yml | test_case.py>")
        sys.exit(1)

    target = sys.argv[1]
    runner = Runner()

    if target.endswith(".yml"):
        runner.run_suite(target)
    elif target.endswith(".py"):
        runner.run_case(target)
    else:
        logger.error("Invalid file. Provide a .yml test suite or .py test case file.")
        sys.exit(1)
