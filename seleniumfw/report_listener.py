# File: core/report_listener.py
import os
import time
from seleniumfw.report_generator import ReportGenerator
from seleniumfw.listener_manager import BeforeTestSuite, AfterTestSuite, BeforeScenario, AfterScenario, BeforeStep, AfterStep, BeforeTestCase, AfterTestCase
from seleniumfw.utils import Logger
import builtins

logger = Logger.get_logger()

# One ReportGenerator per suite
global_report = None
_scenario_start = {}
_steps_info = {}  # key: scenario.name, value: list of step dicts
_step_start = {}  # key: scenario.name, value: start time of current step
_testcase_start = {}
_suite_start = {}
_start_time = {} # Global start time for the suite

@BeforeTestSuite
def init_report(suite_path):
    _suite_start[suite_path] = time.time()
    _start_time[suite_path] = time.time()
    global global_report
    global_report = ReportGenerator(base_dir="reports")
    logger.info(f"Initialized reporting for suite: {suite_path}")
    builtins._active_report = global_report
    # Initialize user.properties if they exist
    user_properties_path = os.path.join("settings", "user.properties")
    if os.path.exists(user_properties_path) is False:
        # create a default user.properties file if it doesn't exist
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
    _steps_info[scenario.name] = []  # initialize clean step list


@BeforeStep
def start_step_timer(context, step):
    scenario_name = context.scenario.name
    _step_start[scenario_name] = time.time()


@AfterStep
def record_step_info(context, step):
    scenario_name = context.scenario.name
    start = _step_start.get(scenario_name, time.time())
    duration = time.time() - start
    step_status = step.status.name if hasattr(step.status, 'name') else str(step.status)

    _steps_info[scenario_name].append({
        "keyword": getattr(step, "keyword", "STEP"),
        "name": step.name,
        "status": step_status.upper(),
        "duration": round(duration, 2)
    })


@AfterScenario
def record_scenario_result(context, scenario):
    scenario_name = scenario.name
    start = _scenario_start.pop(scenario_name, None) or 0
    duration = time.time() - start
    status = scenario.status.name if hasattr(scenario.status, 'name') else str(scenario.status)
    status = status.upper()

    # ✅ Extract tag
    tags = getattr(scenario, 'tags', [])
    category = tags[0] if tags else "Uncategorized"

    # safely remove step info for this scenario
    steps = _steps_info.pop(scenario_name, [])
    feature_name = getattr(scenario, "feature", None)
    feature_name = feature_name.name if feature_name else "Unknown Feature"

    if global_report is None:
        return
    
    global_report.record(
        feature_name,
        scenario_name,
        status,
        round(duration, 2),
        getattr(builtins, "_screenshot_files", []),
        steps,
        category=category  # ✅ pass the tag to ReportGenerator
    )
    logger.info(f"Recorded: {scenario_name} - {status} - {duration:.2f}s")
    builtins._screenshot_files = []



@AfterTestCase
def after_test_case(case, data=None):
    logger.info(f"After test case: {case}")
    testcase_name = case
    start = _testcase_start.pop(testcase_name, None) or 0
    duration = time.time() - start
    # testcase_data = {
    #     "name": testcase_name,
    #     "status": data.get("status", "passed").upper(),
    #     "duration": round(duration, 2),
    # }
    if global_report is None:
        return
    global_report.record_test_case_result(testcase_name, data.get("status", "passed").upper(), round(duration, 2))
    screenshots_dir = global_report.screenshots_dir
    if os.path.exists(screenshots_dir) and os.listdir(screenshots_dir):
        for file in os.listdir(screenshots_dir):
            file_path = os.path.join(screenshots_dir, file)
            if os.path.isfile(file_path):
                global_report.record_screenshot(testcase_name, file_path)

@AfterTestSuite
def finalize_report(suite_path):
    end_time = time.time()
    start = _suite_start.pop(suite_path, None) or 0
    duration = time.time() - start
    global_report.record_overview(suite_path, round(duration, 2), _start_time[suite_path], end_time)
    run_dir = global_report.finalize(suite_path)
    logger.info(f"Report generated at: {run_dir}")
