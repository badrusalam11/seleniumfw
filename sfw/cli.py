import os
import typer
import shutil
from pathlib import Path
from seleniumfw.utils import render_template
from seleniumfw import run

app = typer.Typer()

# Directories for templates
BASE_DIR = Path(__file__).parent
TEMPLATE_PROJECT_DIR = BASE_DIR / "templates" / "project"
TEMPLATE_JINJA_DIR = BASE_DIR / "templates" / "jinja"

@app.command()
def init(project_name: str):
    """Initialize a new SeleniumFW project structure"""
    src = TEMPLATE_PROJECT_DIR

    if project_name in [".", "./"]:
        dest = Path.cwd()
    else:
        dest = Path.cwd() / project_name

        if dest.exists():
            typer.secho(f"❌ Folder already exists: {dest}", fg=typer.colors.RED)
            raise typer.Exit(1)

        dest.mkdir(parents=True, exist_ok=True)

    for item in src.rglob("*"):
        rel_path = item.relative_to(src)
        dest_path = dest / rel_path
        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_path)

    typer.secho(f"✅ Project initialized at {dest}", fg=typer.colors.GREEN)



@app.command()
def create_testsuite(name: str):
    """Create a new testsuite folder and file"""
    path = Path.cwd() / "testsuites" / f"{name}.yml"
    render_template(
        template_name="testsuites/testsuite.yml.j2",
        context={"suite_name": name},
        dest=path,
        base_template_dir=TEMPLATE_JINJA_DIR
    )
    typer.secho(f"✅ Created testsuite: {name}", fg=typer.colors.GREEN)


@app.command()
def create_testcase(name: str):
    """Create a new testcase file"""
    path = Path.cwd() / "testcases" / f"{name}.py"
    render_template(
        template_name="testcases/testcase.py.j2",
        context={"case_name": name},
        dest=path,
        base_template_dir=TEMPLATE_JINJA_DIR
    )
    typer.secho(f"✅ Created testcase: {name}", fg=typer.colors.GREEN)


@app.command()
def create_feature(name: str):
    """Create a new feature file (.feature)"""
    path = Path.cwd() / "include" / "features" / f"{name}.feature"
    render_template(
        template_name="features/feature.feature.j2",
        context={"feature_name": name},
        dest=path,
        base_template_dir=TEMPLATE_JINJA_DIR
    )
    typer.secho(f"✅ Created feature: {name}", fg=typer.colors.GREEN)


@app.command()
def implement_feature(name: str):
    """Generate step definition for given feature"""
    import re
    feature_path = Path.cwd() / "include" / "features" / f"{name}.feature"
    steps_path = Path.cwd() / "include" / "steps" / f"{name}_steps.py"

    if not feature_path.exists():
        typer.secho(f"❌ Feature not found: {feature_path}", fg=typer.colors.RED)
        raise typer.Exit(1)

    steps = ["from behave import given, when, then\n"]
    last_decorator = "when"

    with open(feature_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(("Given", "When", "Then", "And", "*")):
                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue  # skip malformed
                keyword, rest = parts
                decorator = keyword.lower() if keyword.lower() != "and" else last_decorator
                last_decorator = decorator

                # Convert <param> to {param}
                pattern = re.sub(r"<([^>]+)>", r"{\1}", rest)

                # Extract argument names from pattern
                param_names = re.findall(r"{(.*?)}", pattern)
                args = ", ".join(["context"] + param_names)

                steps.append(f"@{decorator}('{pattern}')")
                steps.append(f"def step_impl({args}):")
                steps.append("    pass\n")

    steps_path.parent.mkdir(parents=True, exist_ok=True)
    steps_path.write_text("\n".join(steps))
    typer.secho(f"✅ Implemented feature steps for: {name}", fg=typer.colors.GREEN)



@app.command("run")
def run_command(target: str):
    """Run a suite/case/feature"""
    run(target)


@app.command()
def serve(port: int = typer.Option(None, help="Port to run the server")):
    """Start local SeleniumFW API server."""
    from seleniumfw.api_server import start_server
    start_server(port)

if __name__ == "__main__":
    app()
