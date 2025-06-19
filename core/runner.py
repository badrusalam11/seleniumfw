import os
import time
import yaml
from behave.__main__ import main as behave_main
from core.loader import Loader
from core.utils import Logger
from core.listener_manager import enabled_listeners


class Runner:
    def __init__(self):
        self.logger = Logger.get_logger()
        self.loader = Loader()

    def run_case(self, case_path):
        self.logger.info(f"Running test case: {case_path}")
        full_path = os.path.join("tests", "cases", case_path)
        mod = self.loader.load_module_from_path(full_path)
        if hasattr(mod, "run"):
            mod.run()
        else:
            raise Exception(f"No 'run()' function found in {case_path}")

    def run_suite(self, suite_path):
        # 🔹 BeforeTestuite (before suite starts)
        for hook in enabled_listeners['before_test_suite']:
            hook(suite_path)

        # Load the suite YAML file    
        with open(suite_path) as f:
            suite = yaml.safe_load(f)
        for case in suite.get("test_cases", []):
            self.run_case(case)

        # 🔹 AfterTestSuite (after suite ends)
        for hook in enabled_listeners['after_test_suite']:
            hook(suite_path)

    def run_feature(self, feature_path, tags=None):
        # Run Behave from current working directory (where behave.ini resides)
        self.logger.info(f"is feature {feature_path} exist: {os.path.exists(feature_path)}")
        self.logger.info(f"Running feature: {feature_path} with tags: {tags}")
        args = []
        if tags:
            args.extend(["--tags", tags])
        args.append(feature_path)
        # Behave will auto-load behave.ini in cwd
        behave_main(args)
