# File: core/report_listener.py
import os
import time
import threading
import builtins
from seleniumfw.report_generator import ReportGenerator
from seleniumfw.listener_manager import (
    BeforeTestSuite, AfterTestSuite,
    BeforeScenario, AfterScenario,
    BeforeStep, AfterStep,
    BeforeTestCase, AfterTestCase
)
from seleniumfw.utils import Logger

logger = Logger.get_logger()
_thread_locals = threading.local()
_scenario_start = {}
_steps_info = {}      # key: scenario.name, value: list of step dicts
_step_start = {}      # key: scenario.name, value: start time of current step
_testcase_start = {}  # key: testcase path, value: start time
_suite_start = {}     # key: suite_path, value: start time
_start_time = {}      # key: suite_path, value: global start time

@BeforeTestSuite
def init_report(suite_path):
    # record suite start times
    _suite_start[suite_path] = time.time()
    _start_time[suite_path] = _suite_start[suite_path]

    # create a ReportGenerator for this thread
    rg = ReportGenerator(base_dir="reports")
    _thread_locals.report = rg
    builtins._active_report = rg
    logger.info(f"Initialized reporting for suite: {suite_path}")

    # ensure user.properties exists
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

    # extract category from tags
    tags = getattr(scenario, 'tags', [])
    category = tags[0] if tags else "Uncategorized"

    steps = _steps_info.pop(scenario_name, [])
    feature = getattr(scenario, 'feature', None)
    feature_name = feature.name if feature else "Unknown Feature"

    rg = getattr(_thread_locals, 'report', None)
    if not rg:
        return

    screenshots = getattr(builtins, '_screenshot_files', [])
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
    builtins._screenshot_files = []

@AfterTestCase
def after_test_case(case, data=None):
    logger.info(f"After test case: {case}")
    start = _testcase_start.pop(case, None) or 0
    duration = time.time() - start
    status = data.get('status', 'passed').upper() if data else 'PASSED'

    rg = getattr(_thread_locals, 'report', None)
    if not rg:
        return

    rg.record_test_case_result(case, status, round(duration, 2))
    screenshots_dir = rg.screenshots_dir
    if os.path.exists(screenshots_dir):
        for fname in os.listdir(screenshots_dir):
            path = os.path.join(screenshots_dir, fname)
            if os.path.isfile(path):
                rg.record_screenshot(case, path)

@AfterTestSuite
def finalize_report(suite_path):
    end_time = time.time()
    start = _suite_start.pop(suite_path, None) or 0
    start_time = _start_time.pop(suite_path, None) or start
    duration = end_time - start

    rg = getattr(_thread_locals, 'report', None)
    if not rg:
        return

    rg.record_overview(suite_path, round(duration, 2), start_time, end_time)
    run_dir = rg.finalize(suite_path)
    logger.info(f"Report generated at: {run_dir}")
    # clean up thread-local report
    del _thread_locals.report
