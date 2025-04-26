#!/usr/bin/env python
import re
from subprocess import run
import os
import datetime
import argparse


def merge_svn_git():
    os.chdir(GIT_PATH)
    out = run(["git", "branch", "-a"], capture_output=True, encoding="utf-8")
    out.check_returncode()
    all_branches = out.stdout
    all_branches = [i.strip().lower() for i in all_branches.split("\n") if i != ""]
    svn_branches = []
    local_branches = []
    run(["git", "switch", "-f", "main"]).check_returncode()
    run(["git", "merge", "remotes/git-svn/trunk"]).check_returncode()
    for i in all_branches:
        if "main" in i or "origin" in i or "trunk" in i or "tags" in i:
            continue
        if "git-svn" in i:
            svn_branches.append(i)
        else:
            local_branches.append(i)

    for i in svn_branches:
        lb = i.split("/")[-1]
        if lb not in local_branches:
            run(f"git checkout -b {lb} {i}".split()).check_returncode()
        else:
            run(["git", "switch", "-f", lb]).check_returncode()
            run(["git", "merge", i]).check_returncode()

    out.check_returncode()
    out = run(["git", "branch", "-a"], capture_output=True, encoding="utf-8")
    out.check_returncode()
    out.check_returncode()
    os.chdir(ROOT_PATH)


def parse_git_svn_args():
    global GIT_PATH, NEW_REVISION, REVISION
    os.chdir(GIT_PATH)
    run(["git", "svn", "fetch"], capture_output=True)
    out = run(["git", "svn", "info"], capture_output=True, encoding="utf-8")
    out.check_returncode()
    out = out.stdout
    out = [i.strip().lower() for i in out.split("\n")]
    for i in out:
        # print(i)
        if "revision" in i:
            print(i)
            NEW_REVISION = int(re.findall(r"\d+", i)[0])
        if all([k in i for k in ["last", "changed", "rev"]]):
            print(i)
            REVISION = int(re.findall(r"\d+", i)[0])


def main(root_path: str) -> None:
    rev_str = f"STARTED RUNNING AT {datetime.datetime.now()}"
    print("=" * (len(rev_str) + 5))
    print(rev_str)
    global NEW_REVISION, REVISION, GIT_PATH, SVN_PATH, ROOT_PATH
    ROOT_PATH = root_path
    SVN_PATH = os.path.join(ROOT_PATH, "olex2-gui-svn")
    GIT_PATH = os.path.join(ROOT_PATH, "olex2-gui-git")
    NEW_REVISION = None
    REVISION = None
    print(ROOT_PATH)
    print(f"Current PATH: {os.path.abspath('.')}")
    print(f"listdir: {os.listdir()}")
    print(GIT_PATH)
    parse_git_svn_args()
    if NEW_REVISION == REVISION:
        print(f"No newer revision found, still at {REVISION}")
        print(f"ENDED RUNNING AT {datetime.datetime.now()}")
        print("=" * (len(rev_str) + 5))
        return
    else:
        print(f"Found newer revision than current ({REVISION}): {NEW_REVISION}")
        merge_svn_git()
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
