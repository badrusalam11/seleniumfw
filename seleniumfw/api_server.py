# sfw/api_server.py

from flask import Flask, jsonify, request
import os
import yaml
import subprocess
import sys
import re
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# 1. Project‐relative directories
PROJECT_ROOT = Path.cwd()
BASE_DIR = PROJECT_ROOT / "testsuites"   # <-- now dynamic, under current project
BASE_DIR.mkdir(exist_ok=True)            # ensure folder exists, or you can warn if empty

# 2. Configurable port & server URL
APP_PORT   = int(os.getenv("APP_PORT", 5006))
SERVER_URL = os.getenv("SERVER_URL", f"http://localhost:{APP_PORT}")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", f"http://localhost:3001")

def get_python_interpreter():
    # You could also simply return sys.executable if you don't use venvs
    return sys.executable

PYTHON_EXEC = get_python_interpreter()
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console
        # You can add logging.FileHandler('server.log') to log to file too
    ]
)
logger = logging.getLogger(__name__)


def run_test(testsuite_path, phone_number):
    """Trigger the /api/run endpoint asynchronously."""
    requests.post(
        f"{SERVER_URL}/api/run",
        json={"testsuite_path": testsuite_path, "phone_number": phone_number}
    )

def find_all_yaml_files():
    """Scan BASE_DIR for any .yml/.yaml and return metadata."""
    yaml_files = []
    for full_path in BASE_DIR.rglob("*.yml"):
        relative_path = full_path.relative_to(BASE_DIR)
        logical_path  = f"testsuites/{relative_path.as_posix()}"
        try:
            with open(full_path, "r") as f:
                yml_data = yaml.safe_load(f)
            yaml_files.append({
                "name":    relative_path.as_posix(),
                "path":    logical_path,
                "test_cases": yml_data.get("test_cases", [])
            })
        except Exception as e:
            yaml_files.append({
                "name": logical_path,
                "path": logical_path,
                "error": f"YAML parse error: {e}"
            })
    return yaml_files

@app.route('/api/suites', methods=['GET'])
def list_test_suites():
    return jsonify(find_all_yaml_files())

@app.route('/api/run', methods=['POST'])
def run_suite():
    data = request.get_json() or {}
    ts_path = data.get("testsuite_path", "")
    phone   = data.get("phone_number")

    logger.info(f"Received run request for: {ts_path} (phone: {phone})")

    if not ts_path.startswith("testsuites/"):
        logger.warning("Rejected run: invalid testsuite path")
        return jsonify({"error": "testsuite_path must start with 'testsuites/'"}), 400

    rel = ts_path.removeprefix("testsuites/")
    full = BASE_DIR / rel
    if not full.is_file():
        logger.error(f"Testsuite not found: {ts_path}")
        return jsonify({"error": f"Not found: {ts_path}"}), 404

    try:
        logger.info(f"Running testsuite: {ts_path} using {PYTHON_EXEC}")
        result = subprocess.run(
            [PYTHON_EXEC, "main.py", ts_path],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        logger.info(f"Execution finished. Return code: {result.returncode}")

        stderr = result.stderr
        report_sent = None
        report_path = None
        report_pdf = None

        # Detect report folder path from stderr log
        m = re.search(r"Report generated at: reports[\\/](\d{8}_\d{6})", stderr)
        if m:
            stamp = m.group(1)
            report_path = f"reports/{stamp}"
            report_pdf = PROJECT_ROOT / "reports" / stamp / f"{stamp}.pdf"

            if phone:
                if report_pdf.is_file():
                    try:
                        logger.info(f"Sending report {report_pdf} to WhatsApp number: {phone}")
                        resp = requests.post(
                            f"{WHATSAPP_API_URL.replace(f':{APP_PORT}',':3001')}/send-file",
                            files={"file": (report_pdf.name, open(report_pdf, "rb"), "application/pdf")},
                            data={"chatId": phone, "caption": report_pdf.name}
                        )
                        report_sent = {"status": resp.status_code, "resp": resp.text}
                        logger.info(f"Report sent. Status: {resp.status_code}")
                    except Exception as e:
                        logger.error(f"Failed to send report: {e}")
                        report_sent = {"error": str(e)}
                else:
                    logger.warning(f"Report file not found: {report_pdf}")
                    report_sent = {"error": "PDF not found"}

        return jsonify({
            "stdout":      result.stdout,
            "stderr":      stderr,
            "returncode":  result.returncode,
            "interpreter": PYTHON_EXEC,
            "report_path": str(report_path) if report_path else None,
            "report_pdf":  str(report_pdf) if report_pdf and report_pdf.is_file() else None,
            "report_sent": report_sent
        })
    except Exception as e:
        logger.exception(f"Unexpected error while running suite: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedule', methods=['POST'])
def schedule_suite():
    data = request.get_json() or {}
    ts_path = data.get("testsuite_path", "")
    phone   = data.get("phone_number")
    run_at  = data.get("run_at")

    if not ts_path.startswith("testsuites/"):
        return jsonify({"error": "testsuite_path must start with 'testsuites/'"}), 400
    if not run_at:
        return jsonify({"error": "Missing 'run_at'"}), 400

    try:
        run_dt = datetime.fromisoformat(run_at)
    except Exception as e:
        return jsonify({"error": f"Invalid run_at: {e}"}), 400

    rel = ts_path.removeprefix("testsuites/")
    full = BASE_DIR / rel
    if not full.is_file():
        return jsonify({"error": f"Not found: {ts_path}"}), 404

    job = scheduler.add_job(
        func=run_test,
        trigger='date',
        run_date=run_dt,
        args=[ts_path, phone]
    )
    return jsonify({
        "status": "scheduled",
        "testsuite_path": ts_path,
        "run_at": run_dt.isoformat(),
        "job_id": job.id,
        "phone_number": phone
    })

def start_server(port=None):
    """Entry point for `sfw serve`."""
    final_port = port or APP_PORT
    app.run(host="0.0.0.0", port=final_port, debug=True)
