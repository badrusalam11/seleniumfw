# File: core/listener_manager.py
import importlib
import os
import glob
from core.utils import Logger

logger = Logger.get_logger()

# Global registry for lifecycle hooks
enabled_listeners = {
    'before_test_suite': [],
    'after_test_suite': [],
    'before_feature': [],
    'after_feature': [],
    'before_scenario': [],
    'after_scenario': [],
    'before_step': [],
    'after_step': []
}

# Decorators for users to register hooks

def BeforeTestSuite(func):
    enabled_listeners['before_test_suite'].append(func)
    return func

def AfterTestSuite(func):
    enabled_listeners['after_test_suite'].append(func)
    return func

def BeforeScenario(func):
    enabled_listeners['before_scenario'].append(func)
    return func

def AfterScenario(func):
    enabled_listeners['after_scenario'].append(func)
    return func

def BeforeStep(func):
    enabled_listeners['before_step'].append(func)
    return func

def AfterStep(func):
    enabled_listeners['after_step'].append(func)
    return func

# Auto-discover listener modules

def load_listeners():
    # 1) Load core-provided listeners (e.g., reporting)
    try:
        import core.report_listener
        logger.info("Loaded core.report_listener hooks")
    except ImportError as e:
        logger.warning(f"core.report_listener not found: {e}")

    # 2) Load user-defined listeners under tests/listeners/
    listener_dir = os.path.join(os.getcwd(), "tests", "listeners")
    if os.path.isdir(listener_dir):
        for file in glob.glob(os.path.join(listener_dir, "*.py")):
            mod_name = os.path.basename(file)[:-3]
            if mod_name.startswith("__"):
                continue
            try:
                importlib.import_module(f"tests.listeners.{mod_name}")
                logger.info(f"Loaded test listener: {mod_name}")
            except Exception as ex:
                logger.error(f"Failed to load test listener {mod_name}: {ex}")
    else:
        logger.info("No tests/listeners directory found; skipping user listeners.")

# Initialize on import
load_listeners()
