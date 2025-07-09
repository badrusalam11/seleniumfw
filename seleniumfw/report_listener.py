# File: seleniumfw/report_listener.py

import os
import time
from seleniumfw.report_generator import ReportGenerator
from seleniumfw.listener_manager import (
    BeforeTestSuite, AfterTestSuite,
    BeforeScenario, AfterScenario,
    BeforeStep, AfterStep,
    BeforeTestCase, AfterTestCase
)
from seleniumfw.utils import Logger
from seleniumfw.thread_context import get_context, set_context, clear_context

logger = Logger.get_logger()

_scenario_start = {}
_steps_info = {}
_step_start = {}
_testcase_start = {}
_suite_start = {}
_start_time = {}

@BeforeTestSuite
def init_report(suite_path):
    _suite_start[suite_path] = time.time()
    _start_time[suite_path] = _suite_start[suite_path]

    rg = ReportGenerator(base_dir="reports")
    set_context("report", rg)
    logger.info(f"Initialized reporting for suite: {suite_path}")

    user_properties_path = os.path.join("settings", "user.properties")
    if not os.path.exists(user_properties_path):
        with open(user_properties_path, "w") as f:
            f.write("tester_name= Unknown Tester")

@BeforeTestCase
def before_test_case(case, data=None):
    logger.info(f"Before test case: {case}")
    _testcase_start[case] = time.time()

@BeforeScenario
def start_scenario_timer(context, scenario):
    _scenario_start[scenario.name] = time.time()
    _step_start[scenario.name] = 0
    _steps_info[scenario.name] = []

@BeforeStep
def start_step_timer(context, step):
    scenario_name = context.scenario.name
    _step_start[scenario_name] = time.time()

@AfterStep
def record_step_info(context, step):
    scenario_name = context.scenario.name
    start = _step_start.get(scenario_name, time.time())
    duration = time.time() - start
    status = getattr(step.status, 'name', str(step.status)).upper()
    _steps_info[scenario_name].append({
        "keyword": getattr(step, "keyword", "STEP"),
        "name": step.name,
        "status": status,
        "duration": round(duration, 2)
    })

@AfterScenario
def record_scenario_result(context, scenario):
    scenario_name = scenario.name
    start = _scenario_start.pop(scenario_name, None) or 0
    duration = time.time() - start
    status = getattr(scenario.status, 'name', str(scenario.status)).upper()
    tags = getattr(scenario, 'tags', [])
    category = tags[0] if tags else "Uncategorized"
    steps = _steps_info.pop(scenario_name, [])
    feature = getattr(scenario, 'feature', None)
    feature_name = feature.name if feature else "Unknown Feature"

    rg = get_context("report")
    if not rg:
        return

    screenshots = get_context("screenshots") or []
    rg.record(
        feature_name,
        scenario_name,
        status,
        round(duration, 2),
        screenshots,
        steps,
        category=category
    )

    logger.info(f"Recorded scenario: {scenario_name} - {status} - {duration:.2f}s")

@AfterTestCase
def after_test_case(case, data=None):
    logger.info(f"After test case: {case}")
    start = _testcase_start.pop(case, None) or 0
    duration = time.time() - start
    status = data.get('status', 'passed').upper() if data else 'PASSED'

    rg = get_context("report")
    if not rg:
        return

    rg.record_test_case_result(case, status, round(duration, 2))

    screenshots = get_context("screenshots") or []
    for path in screenshots:
        rg.record_screenshot(case, path)

    api_calls = get_context("api_calls") or []
    if api_calls:
        rg.testcase_api_calls[case] = api_calls

    # cleanup
    set_context("screenshots", [])
    set_context("api_calls", [])

@AfterTestSuite
def finalize_report(suite_path):
    end_time = time.time()
    start = _suite_start.pop(suite_path, None) or 0
    start_time = _start_time.pop(suite_path, None) or start
    duration = end_time - start

    rg = get_context("report")
    if not rg:
        return

    rg.record_overview(suite_path, round(duration, 2), start_time, end_time)
    run_dir = rg.finalize(suite_path)
    logger.info(f"Report generated at: {run_dir}")
