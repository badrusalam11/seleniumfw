# File: core/report_listener.py
import os
import time
from core.report_generator import ReportGenerator
from core.listener_manager import BeforeTestSuite, AfterTestSuite, BeforeScenario, AfterScenario
from core.utils import Logger
import builtins

logger = Logger.get_logger()

# One ReportGenerator per suite
global_report = None
_scenario_start = {}

@BeforeTestSuite
def init_report(suite_path):
    global global_report
    global_report = ReportGenerator(base_dir="reports")
    logger.info(f"Initialized reporting for suite: {suite_path}")
    # attach it to context for step usage
    builtins._active_report = global_report


@BeforeScenario
def start_scenario_timer(context, scenario):
    _scenario_start[scenario.name] = time.time()

@AfterScenario
def record_scenario_result(context, scenario):
    start = _scenario_start.pop(scenario.name, None) or 0
    duration = time.time() - start
    status = scenario.status.name if hasattr(scenario.status, 'name') else str(scenario.status)
    status = status.upper()

    # # Take screenshot if available
    # screenshot_path = None
    # try:
    #     screenshot_name = f"{scenario.name.replace(' ', '_')}.png"
    #     screenshot_dest = os.path.join(global_report.screenshots_dir, screenshot_name)
    #     context.driver.save_screenshot(screenshot_dest)
    #     screenshot_path = screenshot_dest
    # except Exception:
    #     pass
    
    global_report.record(scenario.name, status, duration, builtins._screenshot_files)
    logger.info(f"Recorded: {scenario.name} - {status} - {duration:.2f}s")
    builtins._screenshot_files = []

@AfterTestSuite
def finalize_report(suite_path):
    run_dir = global_report.finalize(suite_path)
    logger.info(f"Report generated at: {run_dir}")
