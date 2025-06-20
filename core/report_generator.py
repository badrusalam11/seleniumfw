# File: core/report_generator.py
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

class ReportGenerator:
    def __init__(self, base_dir="reports"):
        # Create a timestamped folder for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(base_dir, timestamp)
        os.makedirs(self.run_dir, exist_ok=True)
        self.screenshots_dir = os.path.join(self.run_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.json_path = os.path.join(self.run_dir, "result.json")
        self.pdf_path = os.path.join(self.run_dir, "report.pdf")
        # Prepare PDF canvas
        self.c = canvas.Canvas(self.pdf_path, pagesize=letter)
        self.width, self.height = letter
        self.y = self.height - 50
        # Storage for results
        self.results = []

    def record(self, name, status, duration, screenshot_path=None):
        # Store result data and copy screenshot if provided
        rel_screenshot = None
        if screenshot_path and os.path.exists(screenshot_path):
            filename = os.path.basename(screenshot_path)
            dest = os.path.join(self.screenshots_dir, filename)
            with open(screenshot_path, 'rb') as src, open(dest, 'wb') as dst:
                dst.write(src.read())
            rel_screenshot = os.path.join('screenshots', filename)
        self.results.append({
            "name": name,
            "status": status,
            "duration": duration,
            "screenshot": rel_screenshot
        })

    def save_json(self):
        with open(self.json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

    def add_text(self, text, bold=False, size=10):
        font = "Helvetica-Bold" if bold else "Helvetica"
        self.c.setFont(font, size)
        for line in text.split('\n'):
            self.c.drawString(50, self.y, line)
            self.y -= size + 2
            if self.y < 100:
                self.c.showPage()
                self.y = self.height - 50

    def add_table(self):
        # Draw headers
        headers = ["Name", "Status", "Duration", "Screenshot"]
        x_positions = [50, 200, 350, 450]
        self.c.setFont("Helvetica-Bold", 12)
        for x, header in zip(x_positions, headers):
            self.c.drawString(x, self.y, header)
        self.y -= 20
        # Draw rows
        self.c.setFont("Helvetica", 10)
        for item in self.results:
            if self.y < 200:
                self.c.showPage()
                self.y = self.height - 50
            x = 50
            self.c.drawString(x, self.y, item['name']); x += 150
            self.c.drawString(x, self.y, item['status']); x += 150
            self.c.drawString(x, self.y, f"{item['duration']:.2f}s"); x += 150
            if item['screenshot']:
                # Embed thumbnail
                img_path = os.path.join(self.run_dir, item['screenshot'])
                try:
                    img = ImageReader(img_path)
                    self.c.drawImage(img, x, self.y-30, width=80, height=60)
                except Exception:
                    self.c.drawString(x, self.y, "[img]")
            self.y -= 80

    def finalize(self, suite_path):
        # Header
        self.add_text(f"Test Suite Report: {os.path.basename(suite_path)}", bold=True, size=16)
        self.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", size=10)
        self.y -= 10
        # Table of results with screenshots
        self.add_table()
        # Save JSON and PDF
        self.save_json()
        self.c.save()
        return self.run_dir

# Convenience function

def create_suite_report(suite_path, results):
    rg = ReportGenerator()
    for name, status, duration, screenshot in results:
        rg.record(name, status, duration, screenshot)
    return rg.finalize(suite_path)
