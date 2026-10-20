import argparse
import toml


def get_version(pyproject_path="pyproject.toml"):
    with open(pyproject_path, "r", encoding="utf-8") as f:
        pyproject = toml.load(f)
    return pyproject["tool"]["poetry"]["version"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pyproject_path", nargs="?", default="pyproject.toml")
    args = parser.parse_args()
    print(get_version(args.pyproject_path))
