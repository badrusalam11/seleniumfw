from core.runner import Runner

def run():
    runner = Runner()
    runner.run_feature("tests/include/features/login.feature", tags="@positive")
