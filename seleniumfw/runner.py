from concurrent.futures import ThreadPoolExecutor
import os
import time
from dotenv import load_dotenv
import yaml
import inspect
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
    
    def _normalized_path(self, target):
        normalized_path = target.replace('\\', '/').replace('//', '/')
        return normalized_path

    def run_case(self, case_path):
        self.logger.info(f"Running test case: {case_path}")
        mod = self.loader.load_module_from_path(case_path)
        if hasattr(mod, "run"):
            mod.run()
        else:
            raise Exception(f"No 'run()' function found in {case_path}")
        
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
        # 1) Load ONLY the suite-specific hooks for this suite
        load_suite_listeners(suite_path)
        # 🔹 Global BeforeTestSuite hooks
        for hook in enabled_listeners.get('before_test_suite', []):
            self._invoke_hook(hook, suite_path)

        # 🔹 Suite-specific SetUp hooks (@SetUp)
        for hook in enabled_listeners.get('setup', []):
            self._invoke_hook(hook, suite_path)

        # Load the suite YAML
        with open(suite_path) as f:
            suite = yaml.safe_load(f)

        for case in suite.get("test_cases", []):
            case = self._normalized_path(case)
            # 🔹 Per-case SetupTestCase hooks (@SetupTestCase)
            for hook in enabled_listeners.get('setup_test_case', []):
                self._invoke_hook(hook, case, None)

            # 🔹 Global BeforeTestCase hooks
            for hook in enabled_listeners.get('before_test_case', []):
                self._invoke_hook(hook, case)

            # Run the test case and capture status
            status = "passed"
            try:
                self.run_case(case)
            except Exception as e:
                self.logger.error(f"Error running test case {case}: {e}", exc_info=True)
                status = "failed"

            data = {"status": status, "name": case}

            # 🔹 Global AfterTestCase hooks
            for hook in enabled_listeners.get('after_test_case', []):
                self._invoke_hook(hook, case, data)

            # 🔹 Per-case TeardownTestCase hooks (@TeardownTestCase)
            for hook in enabled_listeners.get('teardown_test_case', []):
                self._invoke_hook(hook, case, data)

        # 🔹 Suite-specific Teardown hooks (@Teardown)
        for hook in enabled_listeners.get('teardown', []):
            self._invoke_hook(hook, suite_path)

        # 🔹 Global AfterTestSuite hooks
        for hook in enabled_listeners.get('after_test_suite', []):
            self._invoke_hook(hook, suite_path)

    def run_feature(self, feature_path, tags=None):
        self.logger.info(f"is feature {feature_path} exist: {os.path.exists(feature_path)}")
        self.logger.info(f"Running feature: {feature_path} with tags: {tags}")
        args = []
        if tags:
            args.extend(["--tags", tags])
        args.append(feature_path)

        result_code = behave_main(args)  # <--- Capture the result code
        if result_code != 0:
            self.logger.error(f"Feature run failed with code: {result_code}")
            raise FeatureException(f"Feature run failed with code: {result_code}")
        # You can optionally store this somewhere to use in run_case
        return result_code
    
    
    def run_suite_collection(self, collection_path):
        """
        Run a collection of test suites defined in a single YAML file.
        collection_path: path to collection YAML (with testsuites entries and settings)
        """
        if not os.path.exists(collection_path):
            raise FileNotFoundError(f"Collection file not found: {collection_path}")

        project_root = os.getcwd()
        spec         = yaml.safe_load(open(collection_path))
        method       = spec.get("execution_method", "sequential")
        max_inst     = spec.get("max_concurrent_instances", 1)
        delay        = spec.get("delay_between_instances(s)", 0)
        suites       = spec.get("testsuites", [])

        def _run_suite(path_str):
            suite_path = os.path.join(project_root, path_str)
            self.logger.info(f"▶ Running suite: {suite_path}")
            self.run_suite(suite_path)

        if method == "parallel" and max_inst > 1:
            with ThreadPoolExecutor(max_workers=max_inst) as exe:
                futures = []
                for path_str in suites:
                    futures.append(exe.submit(_run_suite, path_str))
                    time.sleep(delay)
                for f in futures:
                    f.result()
        else:
            for path_str in suites:
                _run_suite(path_str)
                if delay:
                    time.sleep(delay)
