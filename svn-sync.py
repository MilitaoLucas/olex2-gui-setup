#!/usr/bin/env python
import re
from subprocess import run
import os
import datetime
import argparse


def get_commit(revision: int, new_revision: int) -> list:
    command = [
        "git",
        "commit",
        "-m",
        f"Automatic update from revision {revision} to {new_revision}",
    ]
    return command


def rsync_to_git_branch(btname: str = "trunk", tag: bool = False):
    trunk = False
    if btname == "trunk":
        trunk = True
    branch = not (trunk or tag)
    os.chdir(GIT_PATH)
    push = False
    if trunk:
        try:
            out = run("git switch -f main".split(), capture_output=True)
            out.check_returncode()
            out = run(f"rsync -rvP {SVN_PATH}/trunk/ .".split(), capture_output=True)
            if out.returncode != 0:
                print(out.stdout)
                print(out.stderr)
            run("rm -rf .idea".split())
            run("git add .".split())
            run(get_commit(REVISION, NEW_REVISION))
            push = True
        except Exception as e:
            with open(f"{ROOT_PATH}/errors", "a+") as f:
                f.write(f"Error in trunk Syncing: {e}")

    if branch:
        try:
            out = run(f"git switch -f {btname}".split(), capture_output=True)
            out.check_returncode()
            run("rm -rf .idea".split())
            out = run(
                f"rsync -rvP {SVN_PATH}/branches/{btname}/ .".split(),
                capture_output=True,
            )
            if out.returncode != 0:
                print(out.stdout)
                print(out.stderr)
            run("git add .".split())
            run(get_commit(REVISION, NEW_REVISION))
            push = True
        except Exception as e:
            with open(f"{ROOT_PATH}/errors", "a+") as f:
                f.write(f"Error in branch Syncing, branch {btname} afected: {e}")

    if tag:
        try:
            out = run(f"git checkout -b tag_{btname}".split(), capture_output=True)
            out.check_returncode()
            out = run(
                f"rsync -rvP {SVN_PATH}/tags/{btname}/ .".split(), capture_output=True
            )
            if out.returncode != 0:
                print(out.stdout)
                print(out.stderr)
            run(f"rm -rf .idea".split())
            run("git add .".split())
            run(get_commit(REVISION, NEW_REVISION))
            run(f"git switch -f main".split())
            run(f"git tag {btname} tag_{btname}".split())
            run(f"git branch -D tag_{btname}")
            push = True
        except Exception as e:
            with open(f"{ROOT_PATH}/errors", "a+") as f:
                f.write(f"Error in tag Syncing, tag {btname} afected: {e}")
    if push:
        run(f"git push --all origin".split())


def main(root_path: str) -> None:
    print(f"STARTED RUNNING AT {datetime.datetime.now()}")
    global NEW_REVISION, REVISION, GIT_PATH, SVN_PATH, ROOT_PATH
    ROOT_PATH = root_path
    SVN_PATH = os.path.join(ROOT_PATH, "olex2-gui-svn")
    GIT_PATH = os.path.join(ROOT_PATH, "olex2-gui-git")
    NEW_REVISION = None
    REVISION = None

    os.chdir(ROOT_PATH)
    with open("revision", "r") as f:
        REVISION = int(f.read())
    os.chdir(SVN_PATH)
    # Get new patches
    NEW_REVISION = int(
        run(
            "svn info -r HEAD --show-item last-changed-revision".split(),
            capture_output=True,
        ).stdout
    )
    if NEW_REVISION == REVISION:
        return
    with open(os.path.join(ROOT_PATH, "revision"), "w") as f:
        f.write(f"{NEW_REVISION}")
    print(f"Found newer revision than current ({REVISION}): ", int(NEW_REVISION))
    run("svn update".split())
    out = run(
        f"svn diff --summarize -r {REVISION}:{NEW_REVISION}".split(),
        capture_output=True,
    ).stdout
    out = str(out)
    # Extract unique items from each category
    branch_pattern = r"branches/([\d.]+)"
    tag_pattern = r"tags/([\d.]+)"
    trunk_pattern = r"trunk/"

    branches = set(re.findall(branch_pattern, out))
    tags = set(re.findall(tag_pattern, out))
    has_trunk_changes = bool(re.search(trunk_pattern, out))

    # Start Syncing
    for branch in sorted(branches):
        print(f"Syncing to branch: {branch}")
        rsync_to_git_branch(branch)
    for tag in sorted(tags):
        rsync_to_git_branch(tag, tag=True)
        print(f"Syncing to tag: {tag}")
    if has_trunk_changes:
        print("Syncing to trunk")
        rsync_to_git_branch()

    print(f"ENDED RUNNING AT {datetime.datetime.now()}")
    print("=" * 100)
    # --- Update Revision File ---
    # ... (writes the new revision number to REVISION_FILE) ...
    print(f"Updating revision file: {REVISION} to {NEW_REVISION}")
    with open("revision", "w") as f:
        f.write(f"{NEW_REVISION}\n")

    # --- Commit the revision file update ---
    # This commit should happen in the *main* repo (ROOT_PATH), not the GIT_PATH clone
    print(f"Committing revision file update in {ROOT_PATH}")
    os.chdir(ROOT_PATH)  # Change to the repo containing the revision file (Repo-A)
    run(["git", "add", "revision"], check=True)
    commit_msg = f"Update SVN sync revision to {NEW_REVISION}"
    # Check if there are staged changes before committing
    status_result = run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    if "revision" in status_result.stdout:
        run(["git", "commit", "-m", commit_msg], check=True)
        print("Pushing revision file update...")
        # This push uses the default GITHUB_TOKEN permissions for Repo-A
        run(["git", "push"], check=True)
    else:
        print("No changes to revision file to commit.")


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
