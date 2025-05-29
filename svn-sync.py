#!/usr/bin/env python
import re
from subprocess import run, CalledProcessError
import os
import datetime
import argparse
from dotenv import load_dotenv, set_key

load_dotenv()

REVISION = int(os.getenv("REVISION"))
REVISION_15 = int(os.getenv("REVISION_15"))


def apply_for_branch(branch: str):
    run(["git", "checkout", "-f", branch], capture_output=True).check_returncode()
    run(["git", "pull"])
    run(["git", "svn", "fetch"])
    out = run(["git", "svn", "info"], capture_output=True, encoding="utf-8")
    print(f"STDOUT: {out.stdout}, STDERR: {out.stderr}")
    out.check_returncode()
    out = out.stdout
    out = [i.strip().lower() for i in out.split("\n")]
    if branch == "1.5":
        env_name = "REVISION_15"
        revision = REVISION_15
    elif branch == "main":
        env_name = "REVISION"
        revision = REVISION
    else:
        raise Exception(f"Branch {branch} isn't supported")
    for i in out:
        if "revision" in i:
            new_revision = int(re.findall(r"\d+", i)[0])
    if new_revision > revision:
        run(["git", "svn", "rebase"])
        print(
            f"Found newer revision than current ({revision}) for {branch}: {new_revision}"
        )
        run(["git", "push"])
        set_key(os.path.join(ROOT_PATH, ".env"), env_name, str(new_revision))
        return True
    return False


def main(root_path: str) -> None:
    rev_str = f"STARTED RUNNING AT {datetime.datetime.now()}"
    print("=" * (len(rev_str) + 5))
    print(rev_str)
    global GIT_PATH, ROOT_PATH
    ROOT_PATH = root_path
    GIT_PATH = os.path.join(ROOT_PATH, "olex2-gui-git")
    os.chdir(GIT_PATH)
    if not (apply_for_branch("main") or apply_for_branch("1.5")):
        print(f"No new revisions found for any branch")
    print(f"ENDED RUNNING AT {datetime.datetime.now()}")
    print("=" * (len(rev_str) + 5))


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Sync SVN repository changes to a Git repository."
    )
    parser.add_argument(
        "root_path",
        help="The root path containing the script, revision file, SVN checkout, and Git checkout.",
    )
    args = parser.parse_args()

    # Call main with the provided path
    main(args.root_path)
