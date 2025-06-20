# core/browser_factory.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from core.config import Config
import os

class BrowserFactory:
    @staticmethod
    def create_driver():
        cfg = Config()
        browser = cfg.get("browser", "chrome").lower()
        extra_args = cfg.get_list("args")
        print(f"Creating {browser} driver with args: {extra_args}")

        if browser == "chrome":
            options = ChromeOptions()
            for arg in extra_args:
                options.add_argument(arg)
            driver = webdriver.Chrome(options=options)

        elif browser == "firefox":
            options = FirefoxOptions()
            for arg in extra_args:
                # Firefox uses preferences for most things, but
                # headless is a flag, private is a preference:
                if arg == "--headless":
                    options.add_argument(arg)
                elif arg == "--incognito":
                    options.set_preference("browser.privatebrowsing.autostart", True)
                else:
                    options.add_argument(arg)
            driver = webdriver.Firefox(options=options)

        else:
            raise Exception(f"Unsupported browser: {browser}")

        # --- existing screenshot patching logic here ---
        original_save = driver.save_screenshot

        def save_to_report(path, *a, **kw):
            if not os.path.isabs(path):
                from builtins import _active_report
                rpt_dir = _active_report.screenshots_dir
                os.makedirs(rpt_dir, exist_ok=True)
                path = os.path.join(rpt_dir, path)
            return original_save(path, *a, **kw)

        driver.save_screenshot = save_to_report
        return driver
