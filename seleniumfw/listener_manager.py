import importlib
import os
import glob
from seleniumfw.utils import Logger

logger = Logger.get_logger()

# Global registry for lifecycle hooks
enabled_listeners = {
    'before_test_suite': [],
    'after_test_suite': [],
    'setup': [],              # suite-level setup (@SetUp)
    'teardown': [],           # suite-level teardown (@Teardown)
    'before_feature': [],
    'after_feature': [],
    'before_scenario': [],
    'after_scenario': [],
    'before_step': [],
    'after_step': [],
    'before_test_case': [],
    'after_test_case': [],
    'setup_test_case': [],    # per-case setup (@SetupTestCase)
    'teardown_test_case': [], # per-case teardown (@TeardownTestCase)
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

def BeforeTestCase(func):
    enabled_listeners['before_test_case'].append(func)
    return func

def AfterTestCase(func):
    enabled_listeners['after_test_case'].append(func)
    return func

def SetUp(_func=None, *, skipped=True):
    """
    Suite-level setup decorator.
    Usage:
      @SetUp           ← skipped=True by default, so does nothing
      @SetUp(skipped=False)
    """
    def decorator(func):
        if not skipped:
            enabled_listeners['setup'].append(func)
        return func

    # Support both @SetUp and @SetUp(skipped=False)
    if _func:
        return decorator(_func)
    return decorator

def Teardown(_func=None, *, skipped=True):
    """
    Suite-level teardown decorator.
    Usage:
      @Teardown
      @Teardown(skipped=False)
    """
    def decorator(func):
        if not skipped:
            enabled_listeners['teardown'].append(func)
        return func

    if _func:
        return decorator(_func)
    return decorator

def SetupTestCase(_func=None, *, skipped=True):
    """
    Per-test-case setup decorator.
      @SetupTestCase
      @SetupTestCase(skipped=False)
    """
    def decorator(func):
        if not skipped:
            enabled_listeners['setup_test_case'].append(func)
        return func

    if _func:
        return decorator(_func)
    return decorator

def TeardownTestCase(_func=None, *, skipped=True):
    """
    Per-test-case teardown decorator.
      @TeardownTestCase
      @TeardownTestCase(skipped=False)
    """
    def decorator(func):
        if not skipped:
            enabled_listeners['teardown_test_case'].append(func)
        return func

    if _func:
        return decorator(_func)
    return decorator

# Core & user listener discovery (no suite-specific loading here)
def load_core_and_user_listeners():
    # Load built-in listeners
    try:
        import seleniumfw.report_listener
        logger.info("Loaded seleniumfw.report_listener hooks")
    except ImportError:
        logger.warning("No core report_listener found")

    # Load project-level listeners in cwd()/listeners
    listener_dir = os.path.join(os.getcwd(), "listeners")
    logger.info(f"listener_dir: {listener_dir}")
    if os.path.isdir(listener_dir):
        for file in glob.glob(os.path.join(listener_dir, "*.py")):
            name = os.path.splitext(os.path.basename(file))[0]
            if name.startswith("__"): continue
            try:
                importlib.import_module(f"listeners.{name}")
                logger.info(f"Loaded project listener: {name}")
            except Exception as e:
                logger.error(f"Failed loading listener {name}: {e}")
    else:
        logger.info("No project listeners directory; skipping.")

# Suite-specific listener loader called at runtime

def load_suite_listeners(suite_path):
    basename = os.path.splitext(os.path.basename(suite_path))[0]
    suite_module = f"testsuites.{basename}"
    try:
        importlib.import_module(suite_module)
        logger.info(f"Loaded suite listener: {basename}")
    except ImportError as e:
        logger.debug(f"No suite listener {basename}.py found: {e}")
    except Exception as ex:
        logger.error(f"Failed to load suite listener {basename}: {ex}")

# Initialize core and user listeners at import
try:
    load_core_and_user_listeners()
except Exception as e:
    logger.error(f"Error during initial listener loading: {e}")
