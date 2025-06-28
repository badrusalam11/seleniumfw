"""
SeleniumFW - A lightweight Selenium framework with structured runner,
report generator, and POM-based test execution. Inspired by Katalon.
"""

__version__ = "0.1.0"

import sys
from .runner import Runner
from .utils import Logger

def run(target=None):
    logger = Logger.get_logger()

    if not target:
        if len(sys.argv) < 2:
            logger.error("Usage: python main.py <suite_file.yml | test_case.py | file.feature>")
            sys.exit(1)
        target = sys.argv[1]

    runner = Runner()

    if target.endswith(".yml"):
        runner.run_suite(target)
    elif target.endswith(".py"):
        runner.run_case(target)
    elif target.endswith(".feature"):
        runner.run_feature(target)
    else:
        logger.error("Invalid file. Provide a .yml test suite or .py test case file.")
        sys.exit(1)

