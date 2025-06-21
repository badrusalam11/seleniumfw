# File: core/report_listener.py
import os
import time
from core.report_generator import ReportGenerator
from core.listener_manager import BeforeTestSuite, AfterTestSuite, BeforeScenario, AfterScenario, BeforeStep, AfterStep
from core.utils import Logger
import builtins

logger = Logger.get_logger()

# One ReportGenerator per suite
global_report = None
_scenario_start = {}
_steps_info = {}  # key: scenario.name, value: list of step dicts
_step_start = {}  # key: scenario.name, value: start time of current step


@BeforeTestSuite
def init_report(suite_path):
    global global_report
    global_report = ReportGenerator(base_dir="reports")
    logger.info(f"Initialized reporting for suite: {suite_path}")
    builtins._active_report = global_report


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
    # safely remove step info for this scenario
    steps = _steps_info.pop(scenario_name, [])  
    feature_name = getattr(scenario, "feature", None)
    feature_name = feature_name.name if feature_name else "Unknown Feature"

    global_report.record(
        feature_name,
        scenario_name,
        status,
        round(duration, 2),
        getattr(builtins, "_screenshot_files", []),
        steps,
    )
    logger.info(f"Recorded: {scenario_name} - {status} - {duration:.2f}s")
    builtins._screenshot_files = []


@AfterTestSuite
def finalize_report(suite_path):
    run_dir = global_report.finalize(suite_path)
    logger.info(f"Report generated at: {run_dir}")
