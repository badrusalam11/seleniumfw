from core.listener_manager import (
    BeforeTestSuite,
    AfterTestSuite,
    BeforeScenario,
    AfterScenario
)

@BeforeScenario
def before_case(context, scenario):
    print(f"[BeforeScenario] {scenario.name}")

@AfterScenario
def after_case(context, scenario):
    print(f"[AfterScenario] {scenario.name}")

@BeforeTestSuite
def before_suite(suite_path):
    print(f"[BeforeTestSuite] Running: {suite_path}")

@AfterTestSuite
def after_suite(suite_path):
    print(f"[AfterTestSuite] Finished: {suite_path}")
