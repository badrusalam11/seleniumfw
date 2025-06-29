from seleniumfw.listener_manager import SetUp, Teardown, SetupTestCase, TeardownTestCase

@SetUp(skipped=True)
def suite_init():
    pass

@Teardown(skipped=True)
def suite_clean():
    pass

@SetupTestCase(skipped=True)
def case_init(case, data=None):
    pass

@TeardownTestCase(skipped=True)
def case_clean(case, data=None):
    pass
