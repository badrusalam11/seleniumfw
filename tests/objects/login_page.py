class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def enter_username(self, username):
        self.driver.find_element("id", "username").send_keys(username)

    def enter_password(self, password):
        self.driver.find_element("id", "password").send_keys(password)

    def submit(self):
        self.driver.find_element("id", "loginBtn").click()
