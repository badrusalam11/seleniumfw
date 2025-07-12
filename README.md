SeleniumFW 🚀



A lightweight, POM structured test automation framework for Python + Selenium, including:

📦 Project scaffolding with sfw init

⟳ Test suite, test case, feature, and step generation using Jinja2 templating

▶️ Runner for executing feature (.feature), YAML suite, or .py test case files

🌐 REST API server (sfw serve) to list and schedule test suites

🔗 API client module (seleniumfw.api_client) for programmatic integration

⚙️ Typer-powered CLI for all commands

🛡️ Hooks/listener system, dotenv support, jinja templating

🔧 Features

sfw init <project> — bootstrap a complete SeleniumFW project scaffold

sfw create-testsuite <name> — generate boilerplate YAML test suite & .py for its test suite hook

sfw create-testsuite-collection <name> — generate boilerplate YAML test suite collection

sfw create-testcase <name> — generate a .py test case stub

sfw create-listener <name> — generate a test listener

sfw create-feature <name> — generate a .feature file

sfw implement-feature <name> — autogenerate step definitions from your .feature

sfw run <target> — run one of .feature, .yml, or .py test scripts

sfw serve [--port <port>] — expose a REST API to list, run, and schedule test suites

✅ Installation

pip install seleniumfw

Or locally:

git clone https://github.com/badrusalam11/seleniumfw.git
cd seleniumfw
pip install -e .

🚀 Quick Start

1. Scaffold a new project

sfw init myproject
cd myproject

2. Create testsuite/feature/case

sfw create-testsuite login
sfw create-feature login
sfw implement-feature login

3. Add test logic in testcases/, steps/, etc.

4. Run tests

sfw run features/login.feature        # via behave
sfw run testsuites/login.yml         # via runner

🌐 API Testing Example

You can use the same ApiClient to test any public free REST API, for example JSONPlaceholder:

from seleniumfw.api_client import ApiClient

# initialize client for JSONPlaceholder
client = ApiClient(
    base_url="https://jsonplaceholder.typicode.com",
    default_headers={"Accept": "application/json"}
)

# GET a list of posts
response = client.get("/posts")
assert response.status_code == 200
posts = response.json()
assert isinstance(posts, list)
print(f"Retrieved {len(posts)} posts")

# GET a single post
response = client.get("/posts/1")
assert response.status_code == 200
post = response.json()
assert post.get("id") == 1
print(f"Post title: {post.get('title')}")

# POST a new post (will return a mock id)
new_post = {
    "title": "foo",
    "body": "bar",
    "userId": 1
}
response = client.post("/posts", json=new_post)
assert response.status_code == 201
created = response.json()
assert created.get("id") is not None
print(f"Created post ID: {created.get('id')}")

🛠️ Configuration

Use a .env in your project root to customize:

APP_PORT=5006
SERVER_URL=http://localhost:5006

💡 Why use SeleniumFW?

🧠 Inspired by Katalon, but for Python developers

🌟 Supports feature files + step generation + scheduling

🚀 Design for both CLI use and API integration

🧹 Expandable via listeners/hooks, Config, BrowserFactory, etc.

🤝 Contributing

PRs are welcome! Please ensure:

Code is well-documented and follows PEP8

Templates & CLI updated accordingly

README.md and tests updated

Use Black, Flake8, isort (recommended)

📜 License

MIT — see LICENSE for details.

📨 Contact

Built & maintained by Muhamad Badru Salam — QA Automation Engineer (SDET)

Github: [badrusalam11](https://github.com/badrusalam11)

LinkedIn: [Muhamad Badru Salam](https://www.linkedin.com/in/muhamad-badru-salam-3bab2531b/)

Email: muhamadbadrusalam760@gmail.com