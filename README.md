# SeleniumFW 🚀

A lightweight, POM structured test automation framework for **Python + Selenium**, including:

* 📦 **Project scaffolding** with `sfw init`
* ⟳ **Test suite, test case, feature, and step generation** using Jinja2 templating
* ▶️ **Runner** for executing feature (`.feature`), YAML suite, or `.py` test case files
* 🌐 **REST API server** (`sfw serve`) to list and schedule test suites
* ⚙️ **Typer-powered CLI** for all commands
* 🛡️ **Hooks/listener system**, `dotenv` support, jinja templating

---

### 🔧 Features

* `sfw init <project>` — bootstrap a complete SeleniumFW project scaffold
* `sfw create-testsuite <name>` — generate boilerplate YAML test suite & `.py` for its test suite hook
* `sfw create-testcase <name>` — generate a `.py` test case stub
* `sfw create-listener <name>` — generate a test listener
* `sfw create-feature <name>` — generate a `.feature` file
* `sfw implement-feature <name>` — autogenerate step definitions from your `.feature`
* `sfw run <target>` — run one of `.feature`, `.yml`, or `.py` test scripts
* `sfw serve [--port <port>]` — expose a REST API to list, run, and schedule test suites

---

### ✅ Installation

```bash
pip install seleniumfw
```

Or locally:

```bash
git clone https://github.com/badrusalam11/seleniumfw.git
cd seleniumfw
pip install -e .
```

---

### 🚀 Quick Start

#### 1. Scaffold a new project

```bash
sfw init myproject
cd myproject
```

#### 2. Create testsuite/feature/case

```bash
sfw create-testsuite login
sfw create-feature login
sfw implement-feature login
```

#### 3. Add test logic in `testcases/`, `steps/`, etc.

#### 4. Run tests

```bash
sfw run features/login.feature        # via behave
sfw run testsuites/login.yml         # via runner
```

#### 5. REST API server

```bash
sfw serve
curl http://localhost:5006/api/suites
curl -X POST http://localhost:5006/api/run -d '{"testsuite_path":"testsuites/login.yml","phone_number":""}'
```

---

### 🛠️ Configuration

Use a `.env` in your project root to customize:

```ini
APP_PORT=5006
SERVER_URL=http://localhost:5006
```

---

### 💡 Why use SeleniumFW?

* 🧠 Inspired by Katalon, but for **Python developers**
* 🌟 Supports **feature files + step generation + scheduling**
* 🚀 Design for both **CLI use** and **API integration**
* 🧹 Expandable via **listeners/hooks**, `Config`, `BrowserFactory`, etc.

---

### 🤝 Contributing

PRs are welcome! Please ensure:

* Code is well-documented and follows PEP8
* Templates & CLI updated accordingly
* `README.md` and tests updated
* Use Black, Flake8, isort (recommended)

---

### 📜 License

MIT — see [LICENSE](./LICENSE) for details.

---

### 📨 Contact

Built & maintained by **Muhamad Badru Salam** — QA Automation Engineer (SDET)

Github: [badrusalam11](https://github.com/badrusalam11)
LinkedIn: [Muhamad Badru Salam](https://id.linkedin.com/in/muhamad-badru-salam-3bab2531b)
