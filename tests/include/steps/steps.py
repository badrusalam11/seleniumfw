import time
from selenium.webdriver.chrome.options import Options
from behave import given, when, then
from selenium import webdriver

from core.browser_factory import BrowserFactory

@given('the user opens the login page')
def step_open_login(context):
    # options = Options()
    # options.add_argument("--incognito")
    # context.driver = webdriver.Chrome(options=options)
    context.driver = BrowserFactory.create_driver()
    context.driver.get("https://katalon-demo-cura.herokuapp.com/")
    # context.driver.maximize_window()

@when('the user clicks on Make Appointment')
def step_click_make_appointment(context):
    context.driver.find_element("id", "btn-make-appointment").click()

@when('the user enters username "{username}"')
def step_username(context, username):
    context.driver.find_element("id", "txt-username").send_keys(username)

@when('the user enters password "{password}"')
def step_password(context, password):
    context.driver.find_element("id", "txt-password").send_keys(password)

@when('the user clicks login')
def step_login(context):
    context.driver.find_element("id", "btn-login").click()
    time.sleep(3)

@then('the user should see the dashboard')
def step_dashboard(context):
    element = context.driver.find_element("xpath", "//h2[normalize-space()='Make Appointment']")
    context.driver.save_screenshot("dashboard.png")
    
    assert element.is_displayed()
    context.driver.quit()
    
@then('the user should see the error message "{error_message}"')
def step_error_message(context, error_message):
    element = context.driver.find_element("xpath", "//p[@class='lead text-danger']")
    context.driver.save_screenshot("error_message.png")
    
    # get error message text
    assert element.is_displayed()
    assert error_message in element.text

    context.driver.quit()