from core.listener_manager import (
    BeforeTestSuite,
    AfterTestSuite,
    BeforeTestCase,
    AfterTestCase
)

@BeforeTestCase
def before_case(context, scenario):
    print(f"[BeforeTestCase] {scenario.name}")

@AfterTestCase
def after_case(context, scenario):
    print(f"[AfterTestCase] {scenario.name}")

@BeforeTestSuite
def before_suite(suite_path):
    print(f"[BeforeTestSuite] Running: {suite_path}")

@AfterTestSuite
def after_suite(suite_path):
    print(f"[AfterTestSuite] Finished: {suite_path}")
