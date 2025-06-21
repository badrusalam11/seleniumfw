import os
import json
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

class ReportGenerator:
    def __init__(self, base_dir="reports"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        self.run_dir = os.path.join(base_dir, timestamp)
        os.makedirs(self.run_dir, exist_ok=True)
        self.screenshots_dir = os.path.join(self.run_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

        self.json_path = os.path.join(self.run_dir, "cucumber.json")
        self.pdf_path = os.path.join(self.run_dir, f"{timestamp}.pdf")

        self.c = canvas.Canvas(self.pdf_path, pagesize=letter)
        self.width, self.height = letter
        self.y = self.height - 50
        self.results = []
        self.current_page = 1  # Track current page number

    def record(self, feature, scenario, status, duration, screenshot_paths=None, steps_info=None):
        self.results.append({
            "feature": feature,
            "scenario": scenario,
            "status": status,
            "duration": duration,
            "screenshot": screenshot_paths or [],
            "steps": steps_info or []
        })

    def save_json(self):
        with open(self.json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

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
        footer_y = 30  # Position from bottom
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

    def add_feature_section(self, feature_name):
        stripe_height = 25
        self._new_page_if_needed(stripe_height + 60)
        
        # Green feature header with wider margins
        self.c.setFillColor(colors.green)
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
        
        self.c.setFillColor(colors.wheat)
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
            
            # Draw light green background box with NO gap
            self.c.setFillColor(colors.lightgreen)
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
        current_feature = None
        for item in self.results:
            if item['feature'] != current_feature:
                self.add_feature_section(item['feature'])
                current_feature = item['feature']
            self.add_scenario_section(item)
        
        # Add footer to the last page
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