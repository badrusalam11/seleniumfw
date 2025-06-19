import sys
from core.runner import Runner

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <suite_file|test_case>")
        sys.exit(1)

    target = sys.argv[1]
    runner = Runner()

    if target.endswith(".yml"):
        runner.run_suite(target)
    elif target.endswith(".py"):
        runner.run_case(target)
    else:
        print("Invalid file. Provide a .yml test suite or .py test case file.")
