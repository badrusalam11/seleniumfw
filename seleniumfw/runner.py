import os
import time
import yaml
import inspect
from pathlib import Path
from behave.__main__ import main as behave_main
from seleniumfw.loader import Loader
from seleniumfw.utils import Logger
from seleniumfw.listener_manager import enabled_listeners, load_suite_listeners
from seleniumfw.exception import FeatureException
import sys


class Runner:
    def __init__(self):
        self.logger = Logger.get_logger()
        self.loader = Loader()

    def _normalize_path(self, path):
        """Normalize path separators for cross-platform compatibility"""
        return str(Path(path).resolve())

    def run_case(self, case_path):
        # Normalize the path first
        normalized_path = self._normalize_path(case_path)
        self.logger.info(f"Running test case: {normalized_path}")
        
        mod = self.loader.load_module_from_path(normalized_path)
        if hasattr(mod, "run"):
            mod.run()
        else:
            raise Exception(f"No 'run()' function found in {normalized_path}")
        
    def _invoke_hook(self, hook, *args):
        """
        Invoke a hook, matching its signature: if it expects no args, call without args,
        otherwise pass the provided args.
        """
        try:
            sig = inspect.signature(hook)
            if len(sig.parameters) == 0:
                hook()
            else:
                hook(*args)
        except Exception as e:
            self.logger.error(f"Error invoking hook {hook.__name__}: {e}", exc_info=True)

    def run_suite(self, suite_path):
        # Normalize the suite path first
        normalized_suite_path = self._normalize_path(suite_path)
        
        # 1) Load ONLY the suite-specific hooks for this suite
        load_suite_listeners(normalized_suite_path)
        
        # 🔹 Global BeforeTestSuite hooks
        for hook in enabled_listeners.get('before_test_suite', []):
            self._invoke_hook(hook, normalized_suite_path)

        # 🔹 Suite-specific SetUp hooks (@SetUp)
        for hook in enabled_listeners.get('setup', []):
            self._invoke_hook(hook, normalized_suite_path)

        # Load the suite YAML - check if file exists first
        if not os.path.exists(normalized_suite_path):
            raise FileNotFoundError(f"Suite file not found: {normalized_suite_path}")
            
        with open(normalized_suite_path, 'r', encoding='utf-8') as f:
            suite = yaml.safe_load(f)

        for case in suite.get("test_cases", []):
            # Normalize case path if it's a relative path
            case_path = case
            if not os.path.isabs(case):
                # If case is relative, make it relative to the suite file directory
                suite_dir = os.path.dirname(normalized_suite_path)
                case_path = os.path.join(suite_dir, case)
            
            normalized_case_path = self._normalize_path(case_path)
            
            # 🔹 Per-case SetupTestCase hooks (@SetupTestCase)
            for hook in enabled_listeners.get('setup_test_case', []):
                self._invoke_hook(hook, normalized_case_path, None)

            # 🔹 Global BeforeTestCase hooks
            for hook in enabled_listeners.get('before_test_case', []):
                self._invoke_hook(hook, normalized_case_path)

            # Run the test case and capture status
            status = "passed"
            try:
                self.run_case(normalized_case_path)
            except Exception as e:
                self.logger.error(f"Error running test case {normalized_case_path}: {e}", exc_info=True)
                status = "failed"

            data = {"status": status, "name": normalized_case_path}

            # 🔹 Global AfterTestCase hooks
            for hook in enabled_listeners.get('after_test_case', []):
                self._invoke_hook(hook, normalized_case_path, data)

            # 🔹 Per-case TeardownTestCase hooks (@TeardownTestCase)
            for hook in enabled_listeners.get('teardown_test_case', []):
                self._invoke_hook(hook, normalized_case_path, data)

        # 🔹 Suite-specific Teardown hooks (@Teardown)
        for hook in enabled_listeners.get('teardown', []):
            self._invoke_hook(hook, normalized_suite_path)

        # 🔹 Global AfterTestSuite hooks
        for hook in enabled_listeners.get('after_test_suite', []):
            self._invoke_hook(hook, normalized_suite_path)

    def run_feature(self, feature_path, tags=None):
        # Normalize the feature path
        normalized_feature_path = self._normalize_path(feature_path)
        
        self.logger.info(f"is feature {normalized_feature_path} exist: {os.path.exists(normalized_feature_path)}")
        self.logger.info(f"Running feature: {normalized_feature_path} with tags: {tags}")
        
        args = []
        if tags:
            args.extend(["--tags", tags])
        args.append(normalized_feature_path)

        result_code = behave_main(args)  # <--- Capture the result code
        if result_code != 0:
            self.logger.error(f"Feature run failed with code: {result_code}")
            raise FeatureException(f"Feature run failed with code: {result_code}")
        # You can optionally store this somewhere to use in run_case
        return result_code