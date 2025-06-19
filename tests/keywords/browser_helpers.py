from selenium import webdriver

class BrowserHelpers:
    @staticmethod
    def launch_browser():
        return webdriver.Chrome()
