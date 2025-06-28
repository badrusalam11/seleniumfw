import os
import json
import platform
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

from seleniumfw.config import Config

class ReportGenerator:
    def __init__(self, base_dir="reports"):
        self.config = Config()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        self.run_dir = os.path.join(base_dir, timestamp)
        os.makedirs(self.run_dir, exist_ok=True)
        self.screenshots_dir = os.path.join(self.run_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

        self.json_path = os.path.join(self.run_dir, "cucumber.json")
        self.pdf_path = os.path.join(self.run_dir, f"{timestamp}.pdf")
        self.overview_path = os.path.join(self.run_dir, "result.json")
        self.screenshot_path = os.path.join(self.run_dir, "screenshot.json")

        self.c = canvas.Canvas(self.pdf_path, pagesize=letter)
        self.width, self.height = letter
        self.y = self.height - 50
        self.results = []
        self.testcase_result = []  # Track test case results
        self.overview = {}
        self.testcase_screenshots = []  # Track screenshots per test case
        self.current_page = 1  # Track current page number

    def record(self, feature, scenario, status, duration, screenshot_paths=None, steps_info=None,  category="positive"):
        self.results.append({
            "feature": feature,
            "scenario": scenario,
            "status": status,
            "duration": duration,
            "screenshot": screenshot_paths or [],
            "steps": steps_info or [],
            "category": category  # ✅ store tag here
        })

    def record_test_case_result(self, name, status, duration):
        self.testcase_result.append({
            "name": name,
            "status": status,
            "duration": duration
        }) 

    def record_screenshot(self, testcase_name, screenshot_path):
        # Check if testcase entry exists
        for entry in self.testcase_screenshots:
            if entry["testcase_name"] == testcase_name:
                entry["screenshots"].append(screenshot_path)
                return
        # If not found, create new entry
        self.testcase_screenshots.append({
            "testcase_name": testcase_name,
            "screenshots": [screenshot_path]
        })

    def record_overview(self, suite_path, duration, start_time, end_time):
        self.overriew = {
            "testsuite_id": os.path.relpath(suite_path, os.getcwd()),
            "tester_name": self.config.get("tester_name", "Unknown Tester"),
            "environent": self.config.get("environment", "Unknown Environment"),
            "host_name": platform.node(),
            "os": platform.system(),
            "duration": duration,
            "start_time": datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S"),
            "total_testcase": len(self.testcase_result),
            "passed": sum(1 for r in self.testcase_result if r['status'].lower() == 'passed'),
            "failed": sum(1 for r in self.testcase_result if r['status'].lower() == 'failed'),
            "skipped": sum(1 for r in self.testcase_result if r['status'].lower() == 'skipped'),
            "testcase_results": self.testcase_result,
        }

    def save_json(self):
        with open(self.json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        with open(os.path.join(self.overview_path), 'w') as f:
            json.dump(self.overriew, f, indent=2)
        
        with open(os.path.join(self.screenshot_path), 'w') as f:
            json.dump(self.testcase_screenshots, f, indent=2)

    def _new_page_if_needed(self, height_needed=100):
        if self.y < height_needed:
            self._add_footer()  # Add footer before new page
            self.c.showPage()
            self.current_page += 1  # Increment page number
            self.y = self.height - 50

    def _wrap_text(self, text, max_width, font_name, font_size):
        """Improved text wrapping that considers actual text width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def _add_footer(self):
        """Add copyright footer with clickable LinkedIn link and page numbering"""
        footer_y = 20  # Position from bottom
        copyright_text = "© Copyright Muhamad Badru Salam"
        page_text = f"Page {self.current_page}"
        linkedin_url = "https://www.linkedin.com/in/muhamad-badru-salam-3bab2531b/"
        
        # Save current state
        self.c.saveState()
        
        # Set footer font and color
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(colors.grey)
        
        # Calculate positions
        copyright_width = self.c.stringWidth(copyright_text, "Helvetica", 8)
        page_width = self.c.stringWidth(page_text, "Helvetica", 8)
        
        # Center the copyright text
        copyright_x = (self.width - copyright_width) / 2
        
        # Position page number on the right
        page_x = self.width - 50 - page_width
        
        # Draw the copyright footer with clickable LinkedIn link
        self.c.linkURL(linkedin_url, (copyright_x, footer_y - 2, copyright_x + copyright_width, footer_y + 10))
        self.c.drawString(copyright_x, footer_y, copyright_text)
        
        # Draw page number
        self.c.drawString(page_x, footer_y, page_text)
        
        # Restore state
        self.c.restoreState()


    def add_header(self, suite_name):
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawString(50, self.y, f"Test Suite Report: {suite_name}")
        self.y -= 20
        self.c.setFont("Helvetica", 10)
        self.c.drawString(50, self.y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.y -= 30


    def add_section_title(self, title, font_size=14, spacing=10):
            """Draw a bold title and advance the y-cursor."""
            self._new_page_if_needed(font_size + spacing)
            self.c.setFont("Helvetica-Bold", font_size)
            self.c.drawString(50, self.y, title)
            self.y -= (font_size + spacing)
            self.c.setFont("Helvetica", 10)   # reset for following content


    def add_summary_section(self):
        data = self.overriew
        line_h = 15
        left = 50
        mid = 180
        right = 400

        # Make sure we have room
        self._new_page_if_needed(6 * line_h + 20)

        # Block 1: executor, id, environment, host, os
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(left,        self.y,           "Executor")
        self.c.drawString(left,        self.y - line_h,  "ID")
        self.c.drawString(left,        self.y - 2*line_h,"Environment")
        self.c.drawString(left,        self.y - 3*line_h,"Host")
        self.c.drawString(left,        self.y - 4*line_h,"OS")

        self.c.setFont("Helvetica", 10)
        self.c.drawString(mid,         self.y,           data.get("tester_name", "Unknown"))
        self.c.drawString(mid,         self.y - line_h,  data.get("testsuite_id", "Unknown"))
        self.c.drawString(mid,         self.y - 2*line_h,data.get("environent", ""))
        self.c.drawString(mid,         self.y - 3*line_h,data.get("host_name", ""))
        self.c.drawString(mid,         self.y - 4*line_h,data.get("os", ""))

        # Block 2: counts
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(left,        self.y - 6*line_h, "Total")
        self.c.drawString(left,        self.y - 7*line_h, "Passed")
        self.c.drawString(left,        self.y - 8*line_h, "Failed")

        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(colors.black)
        self.c.drawString(mid,         self.y - 6*line_h, str(data.get("total_testcase", 0)))
        self.c.setFillColor(colors.green)
        self.c.drawString(mid,         self.y - 7*line_h, str(data.get("passed", 0)))
        self.c.setFillColor(colors.red)
        self.c.drawString(mid,         self.y - 8*line_h, str(data.get("failed", 0)))

        # Block 3: time info
        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(right,       self.y - 6*line_h, "Start")
        self.c.drawString(right,       self.y - 7*line_h, "End")
        self.c.drawString(right,       self.y - 8*line_h, "Elapsed")

        self.c.setFont("Helvetica", 10)
        self.c.drawString(right + 60,  self.y - 6*line_h, data.get("start_time", ""))
        self.c.drawString(right + 60,  self.y - 7*line_h, data.get("end_time", ""))
        dur = data.get("duration", 0)
        elapsed = f"{int(dur//60)}m - {int(dur%60)}s"
        self.c.drawString(right + 60,  self.y - 8*line_h, elapsed)

        # reset color and move cursor
        self.c.setFillColor(colors.black)
        self.y -= (9 * line_h)
        
    def add_cucumber_summary_table(self):
        left_margin = 50
        table_width = self.width - 100
        row_height = 20

        col_widths = [
            table_width * 0.06,   # #
            table_width * 0.22,   # Feature
            table_width * 0.40,   # Scenario
            table_width * 0.16,   # Category
            table_width * 0.16    # Status
        ]

        # Draw section title
        self.y -= 10
        self.add_section_title("Cucumber Scenario", font_size=12, spacing=8)

        # Header background
        self._new_page_if_needed(row_height + 5)
        self.c.setFillColor(HexColor("#4a90e2"))
        self.c.rect(left_margin, self.y - row_height, table_width, row_height, fill=1, stroke=0)

        # Draw headers
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 11)
        x = left_margin + 5
        for header, w in zip(["#", "Fitur", "Scenario", "Category", "Status"], col_widths):
            self.c.drawString(x, self.y - 15, header)
            x += w
        self.y -= row_height

        # Draw rows
        self.c.setFont("Helvetica", 10)
        for idx, item in enumerate(self.results, 1):
            self._new_page_if_needed(row_height + 5)
            x = left_margin + 5

            # Column 1: #
            self.c.setFillColor(colors.black)
            self.c.drawString(x, self.y - 15, str(idx))
            x += col_widths[0]

            # Column 2: Feature (Fitur)
            self.c.drawString(x, self.y - 15, item["feature"])
            x += col_widths[1]

            # Column 3: Scenario
            self.c.drawString(x, self.y - 15, item["scenario"])
            x += col_widths[2]

            # Column 4: Category (always Positive for now)
            if item.get("category", "positive").lower() == "positive":
                bg_status_color = HexColor("#d6e9c6")
            elif item.get("category", "negative").lower() == "negative":
                bg_status_color = HexColor("#f2dede")
            else:
                bg_status_color = HexColor(colors.lightgrey)
            self.c.setFillColor(bg_status_color)  # light green bg
            self.c.rect(x - 5, self.y - row_height + 3, col_widths[3] - 5, row_height - 6, fill=1, stroke=0)
            self.c.setFillColor(colors.black)
            self.c.drawString(x, self.y - 15, item.get("category", "positive").capitalize())
            x += col_widths[3]

            # Column 5: Status
            status = item["status"].upper()
            color = colors.green if status == "PASSED" else (colors.red if status == "FAILED" else colors.orange)
            self.c.setFillColor(color)
            self.c.drawString(x, self.y - 15, status)

            self.y -= row_height

        self.y -= 10
        self.c.setFillColor(colors.black)


    def add_testcase_table(self):
        # use same margins as your scenario section
        left_margin = 50
        table_width = self.width - 100
        row_height = 20

        # Decide column widths to sum to table_width:
        # e.g. 10% for “#”, 40% for ID, 30% for Duration, 20% for Status
        col_widths = [
            table_width * 0.10,
            table_width * 0.40,
            table_width * 0.30,
            table_width * 0.20,
        ]

        # Header background
        self._new_page_if_needed(row_height + 10)
        self.c.setFillColor(HexColor("#4a90e2"))
        self.c.rect(left_margin, self.y - row_height, table_width, row_height, fill=1, stroke=0)

        # Draw headers
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 11)
        x = left_margin + 5
        for header, w in zip(["#", "ID Testcase", "Duration", "Status"], col_widths):
            self.c.drawString(x, self.y - 15, header)
            x += w
        self.y -= row_height

        # Draw rows
        self.c.setFont("Helvetica", 10)
        for idx, case in enumerate(self.testcase_result, start=1):
            self._new_page_if_needed(row_height + 5)
            x = left_margin + 5
            # Column 1: #
            self.c.setFillColor(colors.black)
            self.c.drawString(x, self.y - 15, str(idx))
            x += col_widths[0]

            # Column 2: ID (wrapped)
            wrapped = self._wrap_text(case['name'], col_widths[1] - 10, "Helvetica", 10)
            self.c.drawString(x, self.y - 15, wrapped[0])
            x += col_widths[1]

            # Column 3: Duration
            dur = case['duration']
            dur_str = f"{int(dur//60)}m - {int(dur%60)}s"
            self.c.drawString(x, self.y - 15, dur_str)
            x += col_widths[2]

            # Column 4: Status (colored)
            status = case['status'].upper()
            color = colors.green if status=="PASSED" else (colors.red if status=="FAILED" else colors.orange)
            self.c.setFillColor(color)
            self.c.drawString(x, self.y - 15, status)
            self.y -= row_height

        # Reset fill color
        self.c.setFillColor(colors.black)
        self.y -= 10

    def add_feature_section(self, feature_name):
        stripe_height = 25
        self._new_page_if_needed(stripe_height + 60)
        
        # Green feature header with wider margins
        self.c.setFillColor(HexColor("#27ab33"))
        self.c.rect(50, self.y - stripe_height, self.width - 100, stripe_height, stroke=0, fill=1)
        
        # White text on green background
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(55, self.y - 18, f"Feature: {feature_name}")
        
        self.y -= stripe_height
        self.c.setFillColor(colors.black)

    def add_scenario_section(self, scenario_data):
        self._new_page_if_needed(200)
        
        # Scenario header with wheat background and wider margins
        scenario_text = f"Scenario: {scenario_data['scenario']} ({scenario_data['status']}, {scenario_data['duration']:.2f}s)"
        title_height = 20
        
        self.c.setFillColor(HexColor("#f4f4dc"))
        self.c.rect(50, self.y - title_height, self.width - 100, title_height, stroke=0, fill=1)
        
        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(55, self.y - 15, scenario_text)
        self.y -= title_height  # Remove extra spacing

        # Steps with consistent formatting and no gaps
        box_width = self.width - 100  # Wider margins
        left_margin = 50
        text_margin = 60  # More space for text
        right_margin = 15
        
        for step in scenario_data['steps']:
            # Calculate text dimensions first
            keyword = step['keyword']
            step_name = step['name']
            duration_text = f"{step['duration']:.2f}s"
            
            # Available width for step text (excluding duration)
            duration_width = self.c.stringWidth(duration_text, "Helvetica", 10)
            available_text_width = box_width - (text_margin - left_margin) - right_margin - duration_width - 20
            
            # Wrap the step text
            full_text = f"{keyword} {step_name}"
            wrapped_lines = self._wrap_text(full_text, available_text_width, "Helvetica", 10)
            
            # Calculate box height based on number of lines
            line_height = 14
            box_height = max(20, len(wrapped_lines) * line_height + 6)
            
            self._new_page_if_needed(box_height + 5)
            
            # Draw yellow green background box with NO gap
            self.c.setFillColor(HexColor("#c7d98d"))  # Soft yellow green
            self.c.rect(left_margin, self.y - box_height, box_width, box_height, stroke=0, fill=1)
            
            # Draw step text
            self.c.setFillColor(colors.black)
            
            # Make keyword bold
            y_text_start = self.y - 10
            current_x = text_margin
            
            # Split first line to make keyword bold
            if wrapped_lines:
                first_line = wrapped_lines[0]
                # Find where keyword ends in the first line
                keyword_end = len(keyword)
                if len(first_line) > keyword_end and first_line[keyword_end] == ' ':
                    # Draw keyword in bold
                    self.c.setFont("Helvetica-Bold", 10)
                    self.c.drawString(current_x, y_text_start, keyword)
                    current_x += self.c.stringWidth(keyword + " ", "Helvetica-Bold", 10)
                    
                    # Draw rest of first line in regular font
                    self.c.setFont("Helvetica", 10)
                    remaining_text = first_line[keyword_end + 1:]
                    self.c.drawString(current_x, y_text_start, remaining_text)
                    
                    # Draw remaining lines
                    for i, line in enumerate(wrapped_lines[1:], 1):
                        self.c.drawString(text_margin, y_text_start - (i * line_height), line)
                else:
                    # If keyword doesn't fit pattern, draw normally
                    self.c.setFont("Helvetica", 10)
                    for i, line in enumerate(wrapped_lines):
                        self.c.drawString(text_margin, y_text_start - (i * line_height), line)
            
            # Draw duration aligned to the right
            self.c.setFont("Helvetica", 10)
            duration_x = left_margin + box_width - right_margin - duration_width
            self.c.drawString(duration_x, y_text_start, duration_text)
            
            self.y -= box_height  # Remove the +2 gap

        # Screenshots: one per row, scalable
        for img_file in scenario_data['screenshot']:
            try:
                img_reader = ImageReader(img_file)
                iw, ih = img_reader.getSize()
                max_w = self.width - 100  # Match the wider margins
                max_h = 300
                scale = min(max_w/iw, max_h/ih)
                w, h = iw*scale, ih*scale
                self._new_page_if_needed(h + 30)
                x = 50  # Match left margin
                y_pos = self.y - h
                self.c.drawImage(img_reader, x, y_pos, width=w, height=h, preserveAspectRatio=True)
                self.y = y_pos - 20
            except Exception:
                self._new_page_if_needed(100)
                self.c.setFillColor(colors.lightgrey)
                self.c.rect(50, self.y - 80, max_w, 80, stroke=0, fill=1)
                self.c.setFillColor(colors.black)
                self.c.drawString(55, self.y - 40, "[img]")
                self.y -= 100

        self.y -= 15
        self.c.setFillColor(colors.black)

    def finalize(self, suite_path):
        suite_name = os.path.basename(suite_path)
        self.add_header(suite_name)
        self.add_summary_section()
        self.add_testcase_table()  # ✅ FIRST: Test Case Table

        # Screenshot-only summary when no cucumber scenarios
        if not self.results and self.testcase_screenshots:
            self.c.showPage()
            self.current_page += 1
            self.y = self.height - 50
            self.add_section_title("Screenshot Attachment", font_size=14, spacing=12)

            left = 50
            line_h = 18
            table_width = self.width - 100
            col_widths = [30, 270, 80, 80]

            # Header row background and white text
            self._new_page_if_needed(line_h + 5)
            self.c.setFillColor(HexColor("#4a90e2"))
            self.c.rect(left, self.y - line_h, table_width, line_h, fill=1, stroke=0)
            self.c.setFillColor(colors.white)
            self.c.setFont("Helvetica-Bold", 11)
            x = left
            for header, w in zip(["#", "Description", "Elapsed", "Status"], col_widths):
                self.c.drawString(x + 5, self.y - 15, header)
                x += w

            self.y -= line_h

            # Data rows without outlines
            self.c.setFont("Helvetica", 10)
            for idx, entry in enumerate(self.testcase_screenshots, start=1):
                name = entry["testcase_name"]
                match = next((r for r in self.testcase_result if r["name"] == name), {})
                dur = match.get("duration", 0)
                elapsed = f"{int(dur//60)}m {int(dur%60)}s"
                status = match.get("status", "").upper()

                self._new_page_if_needed(line_h + 120)
                y_top = self.y

                # Text columns
                self.c.setFillColor(colors.black)
                self.c.drawString(left + 5, y_top - 15, str(idx))
                self.c.drawString(left + col_widths[0] + 5, y_top - 15, name)
                self.c.drawString(left + sum(col_widths[:2]) + 5, y_top - 15, elapsed)
                color = colors.green if status == "PASSED" else (colors.red if status == "FAILED" else colors.orange)
                self.c.setFillColor(color)
                self.c.drawString(left + sum(col_widths[:3]) + 5, y_top - 15, status)
                self.c.setFillColor(colors.black)

                # Draw screenshot image below text
                img_path = entry["screenshots"][-1]
                img = ImageReader(img_path)
                iw, ih = img.getSize()
                max_w = col_widths[1]
                max_h = 100
                scale = min(max_w/iw, max_h/ih)
                w, h = iw*scale, ih*scale
                img_x = left + col_widths[0] + 5
                img_y = y_top - line_h - h - 5
                self.c.drawImage(img, img_x, img_y, width=w, height=h, preserveAspectRatio=True)

                self.y = y_top - line_h - 120 - 10    
        # If we have cucumber results, add the detailed sections cucumber scenarios   
        if self.results:
            self.add_cucumber_summary_table()  # ✅ SECOND: Cucumber Scenario Table

            self.y -= 20
            self.add_section_title("Cucumber Detail", font_size=12, spacing=8)  # ✅ THIRD: Cucumber Detail

            current_feature = None
            for item in self.results:
                if item['feature'] != current_feature:
                    self.add_feature_section(item['feature'])
                    current_feature = item['feature']
                self.add_scenario_section(item)

        self._add_footer()
        self.save_json()
        self.c.save()
        return self.run_dir





# Convenience function
def create_suite_report(suite_path, results):
    rg = ReportGenerator()
    for rec in results:
        rg.record(rec['feature'], rec['scenario'], rec['status'], rec['duration'], rec.get('screenshot'), rec.get('steps'))
    return rg.finalize(suite_path)