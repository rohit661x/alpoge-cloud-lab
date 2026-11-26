"""Install the exact archive manifest revisions without downloading Git history."""
import json
from pathlib import Path
import subprocess


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "lake-manifest.json").read_text())
    for package in manifest["packages"]:
        dest = root / ".lake" / "packages" / package["name"]
        if not dest.exists():
            dest.mkdir(parents=True)
            git(dest, "init", "-q")
            git(dest, "remote", "add", "origin", package["url"])
        if git(dest, "remote", "get-url", "origin") != package["url"]:
            raise RuntimeError(f"Unexpected dependency origin at {dest}")
        head = subprocess.run(["git", "-C", str(dest), "rev-parse", "--verify", "HEAD"],
                              capture_output=True, text=True)
        if head.returncode == 0:
            if head.stdout.strip() != package["rev"]:
                raise RuntimeError(f"Existing dependency at {dest} has a different revision")
        else:
            git(dest, "fetch", "-q", "--depth=1", "--no-tags", "origin", package["rev"])
            git(dest, "checkout", "-q", "--detach", package["rev"])
        print(package["name"], git(dest, "rev-parse", "HEAD"), flush=True)


if __name__ == "__main__":
    main()
