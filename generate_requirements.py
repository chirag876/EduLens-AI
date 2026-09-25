import json
import subprocess
import sys
from importlib.metadata import metadata, version
from urllib.request import urlopen


OUTPUT_FILE = "requirements.txt"


def normalize(name):
    return name.lower().replace("_", "-").replace(".", "-")


def get_dependency_tree():
    result = subprocess.run(
        [sys.executable, "-m", "pipdeptree", "--json-tree"],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def get_pypi_metadata(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


def build_dependency_map(tree):
    dependency_map = {}

    def walk(nodes, parent=None):
        for node in nodes:
            package_data = node.get("package", node)

            package = package_data.get(
                "key",
                package_data.get("project_name")
            )

            if not package:
                continue

            package = normalize(package)

            dependency_map.setdefault(package, set())

            if parent:
                dependency_map[package].add(parent)

            walk(
                node.get("dependencies", []),
                package
            )

    walk(tree)

    return dependency_map


def get_existing_packages():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        return set()

    packages = set()

    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "==" in line:
            package = line.split("==", 1)[0].strip()

            if package:
                packages.add(normalize(package))

    return packages


def get_package_version(package_name):
    try:
        return version(package_name)
    except Exception:
        return "unknown"


def get_package_purpose(package_name):
    data = get_pypi_metadata(package_name)

    summary = data.get("info", {}).get("summary")

    if summary:
        return summary

    try:
        return (
            metadata(package_name).get("Summary")
            or "No description available."
        )
    except Exception:
        return "No description available."


def main():
    print("Reading installed packages...")

    # Get complete dependency tree
    tree = get_dependency_tree()

    # Build package -> parent dependency relationship
    dependency_map = build_dependency_map(tree)

    # Read packages already present in requirements.txt
    existing_packages = get_existing_packages()

    # All currently detected installed packages
    current_packages = set(dependency_map.keys())

    # Only packages that are not already documented
    new_packages = current_packages - existing_packages

    if not new_packages:
        print()
        print("No new packages found.")
        return

    print()
    print(f"Found {len(new_packages)} new package(s).")
    print()

    new_entries = []

    for package in sorted(new_packages):
        print(f"Processing: {package}")

        # Fetch package information from PyPI
        data = get_pypi_metadata(package)
        info = data.get("info", {})

        package_name = info.get(
            "name",
            package
        )

        package_version = get_package_version(package)

        purpose = (
            info.get("summary")
            or get_package_purpose(package)
        )

        # Find parent dependencies
        parents = dependency_map.get(
            package,
            set()
        )

        if parents:
            parent_names = ", ".join(
                sorted(parents)
            )

            dependency_of = (
                f"# Dependency of: {parent_names}"
            )
        else:
            dependency_of = (
                "# Dependency of: "
                "Project / directly installed"
            )

        # Create one clean package block
        entry = (
            f"# {package_name}\n"
            f"# Purpose: {purpose}\n"
            f"{dependency_of}\n"
            f"{package_name}=={package_version}"
        )

        new_entries.append(entry)

    # Append ALL new packages at once
    with open(
        OUTPUT_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        # Separate old content from new content
        file.write("\n\n")

        # Exactly one blank line between packages
        file.write(
            "\n\n".join(new_entries)
        )

        # End file with newline
        file.write("\n")

    print()
    print(f"Updated: {OUTPUT_FILE}")
    print(f"Added: {len(new_packages)} package(s)")


if __name__ == "__main__":
    main()