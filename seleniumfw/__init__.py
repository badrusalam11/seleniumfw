"""
SeleniumFW - A lightweight Selenium framework with structured runner,
report generator, and POM-based test execution. Inspired by Katalon.
"""

__version__ = "0.1.0"

import sys
import os
from .runner import Runner
from .utils import Logger

def run(target=None):
    logger = Logger.get_logger()

    if not target:
        if len(sys.argv) < 2:
            logger.error("Usage: python main.py <test_file>")
            sys.exit(1)
        target = sys.argv[1]

    # Normalize path separators to forward slashes
    normalized_target = target.replace('\\', '/').replace('//', '/')
    
    # Check if file exists
    if not os.path.exists(normalized_target):
        logger.error(f"File not found: {normalized_target}")
        sys.exit(1)

    runner = Runner()

    if normalized_target.endswith(".yml") or normalized_target.endswith(".yaml"):
        runner.run_suite(normalized_target)
    elif normalized_target.endswith(".py"):
        runner.run_case(normalized_target)
    elif normalized_target.endswith(".feature"):
        runner.run_feature(normalized_target)
    else:
        logger.error("Invalid file. Provide a .yml/.yaml test suite, .py test case, or .feature file.")
        sys.exit(1)