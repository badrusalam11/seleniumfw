import time
from selenium.webdriver.chrome.options import Options
from behave import given, when, then
from selenium import webdriver

@given('the user opens the login page')
def step_open_login(context):
    options = Options()
    options.add_argument("--incognito")
    context.driver = webdriver.Chrome(options=options)
    context.driver.get("https://katalon-demo-cura.herokuapp.com/")
    context.driver.maximize_window()

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
    assert element.is_displayed()

    context.driver.quit()