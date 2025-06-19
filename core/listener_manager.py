# core/listener_manager.py
import importlib
import os
import glob

# Global registry
enabled_listeners = {
    'before_test_suite': [],
    'after_test_suite': [],
    'before_feature': [],
    'after_feature': [],
    'before_scenario': [],
    'after_scenario': []
}

# Decorators
def BeforeTestSuite(func):
    enabled_listeners['before_test_suite'].append(func)
    return func

def AfterTestSuite(func):
    enabled_listeners['after_test_suite'].append(func)
    return func

def BeforeTestCase(func):
    enabled_listeners['before_scenario'].append(func)
    return func

def AfterTestCase(func):
    enabled_listeners['after_scenario'].append(func)
    return func

# Auto-discover all modules inside tests/listeners/
def load_all_listeners():
    listener_dir = os.path.join("tests", "listeners")
    for file in glob.glob(os.path.join(listener_dir, "*.py")):
        mod_name = os.path.basename(file)[:-3]
        if mod_name != "listener" and not mod_name.startswith("__"):
            importlib.import_module(f"tests.listeners.{mod_name}")

load_all_listeners()
