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
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp = self.generate_report_name(datetime.now())
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
        self.testcase_api_calls = {}  
    
    def generate_report_name(self, timestamp):
        now = timestamp
        ts_sec = now.strftime("%Y%m%d_%H%M%S")          # e.g. "20250707_221530"
        # ms     = now.strftime("%f")[:3]                 # first 3 digits of microseconds → milliseconds
        # ts     = f"{ts_sec}_{ms}"                       # e.g. "20250707_221530_123"
        return ts_sec

    def record(self, feature, scenario, status, duration, screenshot_paths=None, steps_info=None, category="positive", api_calls=None):
        """Record scenario with screenshots, steps, and API calls"""
        self.results.append({
            "feature": feature,
            "scenario": scenario,
            "status": status,
            "duration": duration,
            "screenshot": screenshot_paths or [],
            "steps": steps_info or [],
            "category": category,
            "api_calls": api_calls or []  # Add API calls to scenario record
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
        """
        Wrap text to fit within max_width.
        - Splits on spaces when possible
        - Chops words longer than max_width into smaller pieces
        """
        if not text:
            return [""]
            
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            # if adding this word still fits, do it
            if self.c.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                # flush the current line
                if current:
                    lines.append(current)
                # now handle the too-long word itself
                if self.c.stringWidth(word, font_name, font_size) <= max_width:
                    # it fits on its own line
                    current = word
                else:
                    # break the word into sub‑chunks
                    part = ""
                    for ch in word:
                        if self.c.stringWidth(part + ch, font_name, font_size) <= max_width:
                            part += ch
                        else:
                            if part:
                                lines.append(part)
                            part = ch
                    current = part
        if current:
            lines.append(current)
        return lines

    def _calculate_row_height(self, texts, col_widths, font_name="Helvetica", font_size=10, min_height=20):
        """Calculate the height needed for a table row based on wrapped text"""
        max_lines = 1
        for text, width in zip(texts, col_widths):
            if text:
                wrapped = self._wrap_text(str(text), width - 10, font_name, font_size)  # -10 for padding
                max_lines = max(max_lines, len(wrapped))
        
        line_height = font_size + 2
        return max(min_height, max_lines * line_height + 10)  # +10 for padding

    def _draw_wrapped_text_in_cell(self, text, x, y, width, font_name="Helvetica", font_size=10, color=colors.black):
        """Draw wrapped text within a cell"""
        self.c.setFont(font_name, font_size)
        self.c.setFillColor(color)
        
        wrapped = self._wrap_text(str(text), width - 10, font_name, font_size)
        line_height = font_size + 2
        
        for i, line in enumerate(wrapped):
            self.c.drawString(x + 5, y - 15 - (i * line_height), line)

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
        header_height = 25
        self._new_page_if_needed(header_height + 5)
        self.c.setFillColor(HexColor("#4a90e2"))
        self.c.rect(left_margin, self.y - header_height, table_width, header_height, fill=1, stroke=0)

        # Draw headers
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 11)
        x = left_margin
        headers = ["#", "Fitur", "Scenario", "Category", "Status"]
        for header, w in zip(headers, col_widths):
            self.c.drawString(x + 5, self.y - 18, header)
            x += w
        self.y -= header_height

        # Draw rows with dynamic heights
        for idx, item in enumerate(self.results, 1):
            # Prepare row data
            row_data = [
                str(idx),
                item["feature"],
                item["scenario"],
                item.get("category", "positive").capitalize(),
                item["status"].upper()
            ]
            
            # Calculate row height based on wrapped text
            row_height = self._calculate_row_height(row_data, col_widths, font_size=10, min_height=25)
            
            # Check if we need a new page
            self._new_page_if_needed(row_height + 5)
            
            # Draw row background for category column
            category = item.get("category", "positive").lower()
            if category == "positive":
                bg_color = HexColor("#d6e9c6")
            elif category == "negative":
                bg_color = HexColor("#f2dede")
            else:
                bg_color = colors.lightgrey
            
            # Draw category background
            cat_x = left_margin + col_widths[0] + col_widths[1] + col_widths[2]
            self.c.setFillColor(bg_color)
            self.c.rect(cat_x, self.y - row_height, col_widths[3], row_height, fill=1, stroke=0)
            
            # Draw cell content
            x = left_margin
            for i, (text, width) in enumerate(zip(row_data, col_widths)):
                if i == 4:  # Status column - colored text
                    status = text
                    color = colors.green if status == "PASSED" else (colors.red if status == "FAILED" else colors.orange)
                    self._draw_wrapped_text_in_cell(text, x, self.y, width, color=color)
                else:
                    self._draw_wrapped_text_in_cell(text, x, self.y, width)
                x += width
            
            self.y -= row_height

        self.y -= 10
        self.c.setFillColor(colors.black)

    def add_testcase_table(self):
        left_margin = 50
        table_width = self.width - 100

        col_widths = [
            table_width * 0.10,   # #
            table_width * 0.50,   # ID (increased width)
            table_width * 0.20,   # Duration
            table_width * 0.20,   # Status
        ]

        # Header background
        header_height = 25
        self._new_page_if_needed(header_height + 10)
        self.c.setFillColor(HexColor("#4a90e2"))
        self.c.rect(left_margin, self.y - header_height, table_width, header_height, fill=1, stroke=0)

        # Draw headers
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 11)
        x = left_margin
        headers = ["#", "ID Testcase", "Duration", "Status"]
        for header, w in zip(headers, col_widths):
            self.c.drawString(x + 5, self.y - 18, header)
            x += w
        self.y -= header_height

        # Draw rows with dynamic heights
        for idx, case in enumerate(self.testcase_result, start=1):
            # Prepare row data
            dur = case['duration']
            dur_str = f"{int(dur//60)}m - {int(dur%60)}s"
            
            row_data = [
                str(idx),
                case['name'],
                dur_str,
                case['status'].upper()
            ]
            
            # Calculate row height based on wrapped text
            row_height = self._calculate_row_height(row_data, col_widths, font_size=10, min_height=25)
            
            # Check if we need a new page
            self._new_page_if_needed(row_height + 5)
            
            # Draw cell content
            x = left_margin
            for i, (text, width) in enumerate(zip(row_data, col_widths)):
                if i == 3:  # Status column - colored text
                    status = text
                    color = colors.green if status == "PASSED" else (colors.red if status == "FAILED" else colors.orange)
                    self._draw_wrapped_text_in_cell(text, x, self.y, width, color=color)
                else:
                    self._draw_wrapped_text_in_cell(text, x, self.y, width)
                x += width
            
            self.y -= row_height

        # Reset fill color
        self.c.setFillColor(colors.black)
        self.y -= 10

    def add_feature_section(self, feature_name):
        # Calculate height needed for wrapped feature name
        full_width = self.width - 100
        wrapped_feature = self._wrap_text(f"Feature: {feature_name}", full_width - 10, "Helvetica-Bold", 12)
        stripe_height = max(25, len(wrapped_feature) * 16 + 10)
        
        self._new_page_if_needed(stripe_height + 60)
        
        # Green feature header with wider margins
        self.c.setFillColor(HexColor("#4a90e2"))
        self.c.rect(50, self.y - stripe_height, full_width, stripe_height, stroke=0, fill=1)
        
        # White text on green background - wrapped
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 12)
        
        # Draw wrapped feature name
        for i, line in enumerate(wrapped_feature):
            self.c.drawString(55, self.y - 18 - (i * 16), line)
        
        self.y -= stripe_height
        self.c.setFillColor(colors.black)

    def add_scenario_section(self, scenario_data):
        # Ensure enough room
        self._new_page_if_needed(200)

        # 1) Wrap the scenario title
        full_width = self.width - 100    # 50px margin each side
        text       = (f"Scenario: {scenario_data['scenario']} "
                    f"({scenario_data['status']}, {scenario_data['duration']:.2f}s)")
        wrapped    = self._wrap_text(text, full_width - 10, "Helvetica-Bold", 11)
        line_h     = 14
        stripe_h   = max(25, len(wrapped) * line_h + 10)  # Increased padding

        # 2) Draw header stripe at current y
        stripe_top = self.y
        stripe_bottom = stripe_top - stripe_h
        if scenario_data['status'].lower() == "passed":
            hex_background = "#f4f4dc"
        else:
            hex_background = "#f26f6f" 
        self.c.setFillColor(HexColor(hex_background))
        self.c.rect(50, stripe_bottom, full_width, stripe_h, stroke=0, fill=1)

        # 3) Draw each wrapped line
        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica-Bold", 11)
        text_x = 55
        # start ~10px down from stripe_top
        start_y = stripe_top - 12
        for i, line in enumerate(wrapped):
            self.c.drawString(text_x, start_y - i*line_h, line)

        # 4) Now move self.y BELOW the stripe (no padding - direct connection)
        self.y = stripe_bottom

        # 5) Draw steps starting from current y
        box_width   = full_width
        left_margin = 50
        text_margin = 60
        right_pad   = 15

        for step in scenario_data['steps']:
            keyword = step['keyword']
            name    = step['name']
            dur_txt = f"{step['duration']:.2f}s"

            # calculate height & wrap
            dur_w   = self.c.stringWidth(dur_txt, "Helvetica", 10)
            avail_w = box_width - (text_margin - left_margin) - right_pad - dur_w - 20
            lines   = self._wrap_text(f"{keyword} {name}", avail_w, "Helvetica", 10)
            step_h  = max(25, len(lines) * line_h + 10)  # Increased minimum height

            # page break if needed
            self._new_page_if_needed(step_h + 5)

            # draw step background
            if step['status'].lower() == "passed":
                hex_background = "#c7d98d"
            elif step['status'].lower() == "failed":
                hex_background = "#f5b0b0"
            else: 
                hex_background="#e3dede"
            self.c.setFillColor(HexColor(hex_background))
            self.c.rect(left_margin, self.y - step_h, box_width, step_h, stroke=0, fill=1)

            # draw text + bold keyword
            y0 = self.y - 12
            x0 = text_margin

            # first line: bold keyword
            first = lines[0]
            if first.startswith(keyword + " "):
                self.c.setFont("Helvetica-Bold", 10)
                self.c.setFillColor(colors.black)
                self.c.drawString(x0, y0, keyword)
                kw_w = self.c.stringWidth(keyword + " ", "Helvetica-Bold", 10)
                self.c.setFont("Helvetica", 10)
                self.c.drawString(x0 + kw_w, y0, first[len(keyword)+1:])
            else:
                self.c.setFont("Helvetica", 10)
                self.c.setFillColor(colors.black)
                self.c.drawString(x0, y0, first)

            # additional lines
            self.c.setFont("Helvetica", 10)
            for idx, ln in enumerate(lines[1:], start=1):
                self.c.drawString(text_margin, y0 - idx*line_h, ln)

            # duration at right
            self.c.drawString(
                left_margin + box_width - right_pad - dur_w,
                y0,
                dur_txt
            )

            # advance y position
            self.y -= step_h
            
        # 6) API Calls: Display scenario-specific API calls AFTER steps
        scenario_api_calls = scenario_data.get('api_calls', [])
        if scenario_api_calls:
            self.add_api_section(scenario_api_calls, f"API Calls for Scenario: {scenario_data['scenario']}")
            
        # 7) Screenshots: Display AFTER steps and API calls
        if scenario_data.get('screenshot'):
            # Add some spacing before screenshots
            self.y -= 10
            
            max_w = self.width - 100  # Define max_w for screenshots
            max_h = 300
            
            for img_file in scenario_data['screenshot']:
                try:
                    img_reader = ImageReader(img_file)
                    iw, ih = img_reader.getSize()
                    scale = min(max_w/iw, max_h/ih)
                    w, h = iw*scale, ih*scale
                    
                    # Check if we need a new page for this screenshot
                    self._new_page_if_needed(h + 30)
                    
                    x = 50  # Match left margin
                    y_pos = self.y - h
                    self.c.drawImage(img_reader, x, y_pos, width=w, height=h, preserveAspectRatio=True)
                    self.y = y_pos - 20  # Add spacing after screenshot
                    
                except Exception as e:
                    # Handle image loading errors
                    placeholder_h = 80
                    self._new_page_if_needed(placeholder_h + 30)
                    self.c.setFillColor(colors.lightgrey)
                    self.c.rect(50, self.y - placeholder_h, max_w, placeholder_h, stroke=0, fill=1)
                    # Add error text
                    self.c.setFillColor(colors.red)
                    self.c.setFont("Helvetica", 10)
                    self.c.drawString(55, self.y - placeholder_h/2, f"Failed to load image: {os.path.basename(img_file)}")
                    # Reset fill color and update position
                    self.c.setFillColor(colors.black)
                    self.y -= (placeholder_h + 20)

        # 8) Add spacing before next scenario
        self.y -= 15
        self.c.setFillColor(colors.black)

    METHOD_COLORS = {
        "GET":    HexColor("#61affe"),
        "POST":   HexColor("#49cc90"),
        "PUT":    HexColor("#fca130"),
        "DELETE": HexColor("#f93e3e"),
        "PATCH":  HexColor("#50e3c2"),
    }

    def add_api_section(self, api_calls, section_title=None):
        """
        ✅ REUSABLE method for displaying API calls
        Can be called from both scenarios and test cases
        """
        if not api_calls:
            return

        # Add section title if provided
        if section_title:
            self.y -= 10
            self.add_section_title(section_title, font_size=10, spacing=6)

        for call in api_calls:
            method = call.get("method", "").upper()
            url = call.get("url", "")
            req = call.get("kwargs", {})
            resp = call.get("response_body", "")

            margin = 50
            full_width = self.width - 2*margin
            badge_w = 50
            text_x = margin + badge_w + 5
            wrap_width = full_width - badge_w - 10

            # 1) Header
            header_h = 20
            self._new_page_if_needed(header_h + 200)
            # border
            self.c.setStrokeColor(self.METHOD_COLORS.get(method, colors.black))
            self.c.rect(margin, self.y - header_h, full_width, header_h, fill=0)
            # badge
            self.c.setFillColor(self.METHOD_COLORS.get(method, colors.black))
            self.c.rect(margin, self.y - header_h, badge_w, header_h, fill=1, stroke=0)
            self.c.setFillColor(colors.white)
            self.c.setFont("Helvetica-Bold", 9)
            self.c.drawCentredString(margin + badge_w/2, self.y - header_h + 5, method)
            # URL (wrapped)
            self.c.setFillColor(colors.black)
            self.c.setFont("Helvetica", 8)
            url_lines = self._wrap_text(url, wrap_width, "Helvetica", 8)
            for i, line in enumerate(url_lines):
                self.c.drawString(text_x, self.y - header_h + 5 - i*10, line)
            # step down
            self.y -= (header_h + 5)

            # 2) Request box (light blue) - ULTRA STRICT WIDTH CONTROL
            if req:
                if "json" in req:
                    payload = json.dumps(req["json"], ensure_ascii=False)
                else:
                    payload = str(req.get("data", ""))
                
                if payload and payload.strip():
                    # ✅ MAXIMUM WIDTH SAFETY - Batas width sangat ketat
                    max_content_width = full_width - 100  # Margin super besar
                    
                    # Split payload into manageable chunks if too long
                    if len(payload) > 300:  # Limit panjang payload
                        payload = payload[:300] + "... (truncated)"
                    
                    req_lines = []
                    words = payload.split()
                    current_line = ""
                    
                    for word in words:
                        test_line = f"{current_line} {word}".strip()
                        # ✅ STRICT WIDTH CHECK - Cek width setiap kata
                        if self.c.stringWidth(test_line, "Helvetica", 7) <= max_content_width:
                            current_line = test_line
                        else:
                            if current_line:
                                req_lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        req_lines.append(current_line)
                    
                    req_h = 12 + len(req_lines)*8
                    self._new_page_if_needed(req_h + 20)
                    
                    self.c.setFillColor(HexColor("#e3f2fd"))
                    self.c.rect(margin, self.y - req_h, full_width, req_h, fill=1, stroke=0)
                    self.c.setFillColor(colors.black)
                    self.c.setFont("Helvetica-Bold", 8)
                    self.c.drawString(margin + 5, self.y - 12, "Request:")
                    self.c.setFont("Helvetica", 7)
                    
                    for i, line in enumerate(req_lines):
                        x_pos = margin + 60
                        y_pos = self.y - 12 - i*8
                        # ✅ FINAL SAFETY CHECK - Potong jika masih terlalu panjang
                        while self.c.stringWidth(line, "Helvetica", 7) > max_content_width and len(line) > 10:
                            line = line[:-10] + "..."
                        self.c.drawString(x_pos, y_pos, line)
                    
                    self.y -= (req_h + 5)

            # 3) Response box (light green) - ULTRA STRICT WIDTH CONTROL
            if resp and resp.strip():
                # ✅ MAXIMUM WIDTH SAFETY - Batas width sangat ketat
                max_content_width = full_width - 100  # Margin super besar
                
                # Split response into manageable chunks if too long
                if len(resp) > 300:  # Limit panjang response
                    resp = resp[:300] + "... (truncated)"
                
                resp_lines = []
                words = resp.split()
                current_line = ""
                
                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    # ✅ STRICT WIDTH CHECK - Cek width setiap kata
                    if self.c.stringWidth(test_line, "Helvetica", 7) <= max_content_width:
                        current_line = test_line
                    else:
                        if current_line:
                            resp_lines.append(current_line)
                        current_line = word
                
                if current_line:
                    resp_lines.append(current_line)
                
                resp_h = 12 + len(resp_lines)*8
                self._new_page_if_needed(resp_h + 20)
                
                self.c.setFillColor(HexColor("#e8f5e9"))
                self.c.rect(margin, self.y - resp_h, full_width, resp_h, fill=1, stroke=0)
                self.c.setFillColor(colors.black)
                self.c.setFont("Helvetica-Bold", 8)
                self.c.drawString(margin + 5, self.y - 12, "Response:")
                self.c.setFont("Helvetica", 7)
                
                for i, line in enumerate(resp_lines):
                    x_pos = margin + 60
                    y_pos = self.y - 12 - i*8
                    # ✅ FINAL SAFETY CHECK - Potong jika masih terlalu panjang
                    while self.c.stringWidth(line, "Helvetica", 7) > max_content_width and len(line) > 10:
                        line = line[:-10] + "..."
                    self.c.drawString(x_pos, y_pos, line)
                
                self.y -= (resp_h + 15)
                self._new_page_if_needed(50)

    def add_api_section_for_test_case(self, case_name):
        """
        ✅ WRAPPER method for test case API calls
        Uses the generic add_api_section method
        """
        calls = self.testcase_api_calls.get(case_name, [])
        if not calls:
            return

        # Add spacing and call the generic method
        self.y -= 15
        self.add_api_section(calls, f"API Calls for {case_name}")

    def finalize(self, suite_path):
        suite_name = os.path.basename(suite_path)
        
        # 1. Add header
        self.add_header(suite_name)
        
        # 2. Add summary section
        self.add_summary_section()
        
        # 3. Add test case table (always first)
        self.add_testcase_table()

        # 4. If we have cucumber results, add cucumber sections
        if self.results:
            # Add cucumber summary table
            self.add_cucumber_summary_table()
            
            # Add detailed cucumber scenarios
            self.y -= 20
            self.add_section_title("Cucumber Detail", font_size=12, spacing=8)

            # Group scenarios by feature and display them properly
            current_feature = None
            for item in self.results:
                # Add feature header if this is a new feature
                if item['feature'] != current_feature:
                    if current_feature is not None:  # Add spacing between features
                        self.y -= 20
                    self.add_feature_section(item['feature'])
                    current_feature = item['feature']
                
                # Add the scenario with its steps and screenshots
                self.add_scenario_section(item)

        # 5. Screenshot-only summary when no cucumber scenarios but we have screenshots
        elif self.testcase_screenshots:
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
                if entry["screenshots"]:
                    img_path = entry["screenshots"][-1]
                    try:
                        img = ImageReader(img_path)
                        iw, ih = img.getSize()
                        max_w = col_widths[1]
                        max_h = 100
                        scale = min(max_w/iw, max_h/ih)
                        w, h = iw*scale, ih*scale
                        img_x = left + col_widths[0] + 5
                        img_y = y_top - line_h - h - 5
                        self.c.drawImage(img, img_x, img_y, width=w, height=h, preserveAspectRatio=True)
                    except Exception:
                        # Draw placeholder if image fails to load
                        self.c.setFillColor(colors.lightgrey)
                        self.c.rect(left + col_widths[0] + 5, y_top - line_h - 50, col_widths[1], 50, fill=1, stroke=0)
                        self.c.setFillColor(colors.black)

                self.y = y_top - line_h - 120 - 10    

        # 6. Add API sections for each test case
        # ✅ Only show test case API calls if no scenarios have API calls
        has_scenario_api_calls = any(item.get('api_calls') for item in self.results)
        if not has_scenario_api_calls:
            for case in (c["name"] for c in self.testcase_result):
                self.add_api_section_for_test_case(case)
        
        # 7. Add footer and save
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