import re
import toml

def get_dependecies():
    with open("pyproject.toml", "r") as f:
        pyproject = toml.load(f)
    return pyproject["tool"]["poetry"]["dependencies"]

def convert_dependencies_to_string(dependencies):
    """Convert dependencies dictionary to a pip-compatible string."""
    def normalize_version(value):
        if value.startswith("^") or value.startswith("~"):
            return value[1:]
        return value

    def get_operator(value):
        if value.startswith(("^", "~")):
            return ">="
        elif value.startswith(("=", ">", "<", "!")):
            return ""
        else:
            return "=="

    return ' '.join(
        f"{key}{get_operator(value)}{normalize_version(value) if get_operator(value) != '' else value}"
        for key, value in dependencies.items()
        if isinstance(value, str) and not key.startswith("python")
    )

if __name__ == "__main__":
    print(convert_dependencies_to_string(get_dependecies()))