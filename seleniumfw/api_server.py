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

# 1. Project‐relative directories for single suites and collections
PROJECT_ROOT = Path.cwd()
DIR_MAP = {
    "testsuites": PROJECT_ROOT / "testsuites",
    "testsuite_collections": PROJECT_ROOT / "testsuite_collections",
}
# Ensure directories exist
for d in DIR_MAP.values():
    d.mkdir(exist_ok=True)

# 2. Configurable ports & URLs
APP_PORT        = int(os.getenv("APP_PORT", 5006))
SERVER_URL      = os.getenv("SERVER_URL", f"http://localhost:{APP_PORT}")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", f"http://localhost:3001")


def get_python_interpreter():
    return sys.executable

PYTHON_EXEC = get_python_interpreter()

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def run_test(testsuite_path, phone_number):
    """Trigger the /api/run endpoint asynchronously."""
    requests.post(
        f"{SERVER_URL}/api/run",
        json={"testsuite_path": testsuite_path, "phone_number": phone_number}
    )


def find_all_yaml_files():
    """Scan both directories for .yml/.yaml and return metadata."""
    yaml_files = []
    for key, base_dir in DIR_MAP.items():
        for full_path in base_dir.rglob("*.yml"):
            rel = full_path.relative_to(base_dir)
            logical_path = f"{key}/{rel.as_posix()}"
            try:
                yml_data = yaml.safe_load(full_path.read_text())
                yaml_files.append({
                    "name":       rel.as_posix(),
                    "path":       logical_path,
                    "test_cases": yml_data.get("test_cases", []),
                    "testsuites": yml_data.get("testsuites")
                })
            except Exception as e:
                yaml_files.append({
                    "name":  rel.as_posix(),
                    "path":  logical_path,
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

    # Validate prefix and resolve path
    parts = ts_path.split('/', 1)
    if len(parts) != 2 or parts[0] not in DIR_MAP:
        logger.warning("Rejected run: invalid testsuite path prefix")
        return jsonify({"error": f"testsuite_path must start with one of {list(DIR_MAP.keys())}/"}), 400

    key, rel = parts
    full = DIR_MAP[key] / rel
    if not full.is_file():
        logger.error(f"Testsuite not found: {ts_path}")
        return jsonify({"error": f"Not found: {ts_path}"}), 404

    # Build command: main.py will handle single vs. collection
    cmd = [PYTHON_EXEC, "main.py", ts_path]

    try:
        logger.info(f"Running testsuite: {ts_path} using {PYTHON_EXEC}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        logger.info(f"Execution finished. Return code: {result.returncode}")

        stderr = result.stderr
        reports = []

        # Detect all report folder stamps from stderr log
        stamps = re.findall(r"Report generated at: reports[\\/](\d{8}_\d{6})", stderr)
        for stamp in stamps:
            report_dir = PROJECT_ROOT / "reports" / stamp
            report_pdf = report_dir / f"{stamp}.pdf"
            sent_status = None

            if phone and report_pdf.is_file():
                try:
                    logger.info(f"Sending report {report_pdf} to WhatsApp number: {phone}")
                    resp = requests.post(
                        f"{WHATSAPP_API_URL.replace(f':{APP_PORT}',':3001')}/send-file",
                        files={"file": (report_pdf.name, open(report_pdf, "rb"), "application/pdf")},
                        data={"chatId": phone, "caption": report_pdf.name}
                    )
                    sent_status = {"status": resp.status_code, "resp": resp.text}
                    logger.info(f"Report sent. Status: {resp.status_code}")
                except Exception as e:
                    logger.error(f"Failed to send report: {e}")
                    sent_status = {"error": str(e)}
            elif phone:
                sent_status = {"error": "PDF not found or not a collection"}

            reports.append({
                "stamp":       stamp,
                "report_path": str(report_dir),
                "report_pdf":  str(report_pdf) if report_pdf.is_file() else None,
                "sent":        sent_status
            })

        return jsonify({
            "stdout":      result.stdout,
            "stderr":      stderr,
            "returncode":  result.returncode,
            "interpreter": PYTHON_EXEC,
            "reports":     reports
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

    logger.info(f"Scheduling run for: {ts_path} at {run_at} (phone: {phone})")

    # Validate prefix and resolve path
    parts = ts_path.split('/', 1)
    if len(parts) != 2 or parts[0] not in DIR_MAP:
        return jsonify({"error": f"testsuite_path must start with one of {list(DIR_MAP.keys())}/"}), 400
    if not run_at:
        return jsonify({"error": "Missing 'run_at'"}), 400

    try:
        run_dt = datetime.fromisoformat(run_at)
    except Exception as e:
        return jsonify({"error": f"Invalid run_at: {e}"}), 400

    key, rel = parts
    full = DIR_MAP[key] / rel
    if not full.is_file():
        return jsonify({"error": f"Not found: {ts_path}"}), 404

    job = scheduler.add_job(
        func=run_test,
        trigger='date',
        run_date=run_dt,
        args=[ts_path, phone]
    )
    return jsonify({
        "status":        "scheduled",
        "testsuite_path": ts_path,
        "run_at":         run_dt.isoformat(),
        "job_id":         job.id,
        "phone_number":   phone
    })


def start_server(port=None):
    final_port = port or APP_PORT
    app.run(host="0.0.0.0", port=final_port, debug=True)
