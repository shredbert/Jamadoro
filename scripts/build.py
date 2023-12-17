#!.venv/bin/python3
import subprocess, sys

"""
Script to build project on server by building static assets & installing latest Python modules.
Database schema must be reloaded manually to avoid data loss.
"""


def main(reload_schema):
    print("Syncing repo...")

    sync_repo = subprocess.run(["git", "pull"], capture_output=True).returncode

    if sync_repo != 0:
        print("Error syncing repo")
        sys.exit(1)

    print("Repo synced")

    print("Building static assets...")

    build_static_assets = subprocess.run(
        ["npm", "run", "build"], capture_output=True
    ).returncode

    if build_static_assets != 0:
        print("Error building static assets")
        sys.exit(1)

    print("Static asset built successfully")

    print("Installing latest packages...")

    install_python_packages = subprocess.run(
        [".venv/bin/pip", "install", "-r", "requirements.txt"], capture_output=True
    ).returncode

    if install_python_packages != 0:
        print("Error installing latest packages")
        sys.exit(1)

    print("Latest packages installed")

    if not reload_schema:
        print("Skipping schema reload")
        return

    print("Installing latest packages...")

    schema_reload = subprocess.run(
        ["psql", "-d", "jamadoro", "-c", "\ir ./scripts/load-schema.sql"], capture_output=True
    ).returncode

    if schema_reload != 0:
        print("Error reloading schema")
        sys.exit(1)

    print("Schema reloaded")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["schema-reload", "no-schema-reload"]:
        print("Usage: ./build.py [schema-reload/no-schema-reload]")
        sys.exit(1)

    main(reload_schema=True if sys.argv[1] == "schema-reload" else False)
