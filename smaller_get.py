#!/usr/bin/env python
import re
from subprocess import run, CalledProcessError
import os
import datetime
import argparse
import sys
from dotenv import load_dotenv, set_key

load_dotenv()

REVISION = int(os.getenv("REVISION", "0"))
REVISION_15 = int(os.getenv("REVISION_15", "0"))


def check_git_svn_available():
    """Check if git-svn is available in the system."""
    result = run(["git", "svn", "--version"], capture_output=True)
    return result.returncode == 0


def apply_for_branch(branch: str):
    try:
        run(["git", "checkout", "-f", branch], capture_output=True).check_returncode()
        run(["git", "pull"])
        run(["git", "svn", "fetch"])
        out = run(["git", "svn", "info"], capture_output=True, encoding="utf-8")
        
        if out.returncode != 0:
            print(f"Warning: git svn info failed for branch {branch}")
            print(f"STDOUT: {out.stdout}")
            print(f"STDERR: {out.stderr}")
            print("Skipping this branch - git-svn may not be properly initialized")
            return False
        
        out_text = out.stdout
        out = [i.strip().lower() for i in out_text.split("\n")]
        if branch == "1.5":
            env_name = "REVISION_15"
            revision = REVISION_15
        elif branch == "main":
            env_name = "REVISION"
            revision = REVISION
        else:
            raise Exception(f"Branch {branch} isn't supported")
        
        new_revision = None
        for i in out:
            if "revision" in i:
                matches = re.findall(r"\d+", i)
                if matches:
                    new_revision = int(matches[0])
                    break
        
        if new_revision is None:
            print(f"Warning: Could not find revision information for branch {branch}")
            return False
        
        if new_revision > revision:
            run(["git", "svn", "rebase"])
            print(
                f"Found newer revision than current ({revision}) for {branch}: {new_revision}"
            )
            run(["git", "push"])
            set_key(os.path.join(ROOT_PATH, ".env"), env_name, str(new_revision))
            return True
        return False
    except CalledProcessError as e:
        print(f"Error processing branch {branch}: {e}")
        print(f"Command: {e.cmd}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def main(root_path: str) -> None:
    rev_str = f"STARTED RUNNING AT {datetime.datetime.now()}"
    print("=" * (len(rev_str) + 5))
    print(rev_str)
    
    # Check if git-svn is available
    if not check_git_svn_available():
        print("ERROR: git-svn is not installed or not available in PATH")
        print("Please install git-svn to use this script")
        print("On Ubuntu/Debian: sudo apt-get install git-svn")
        print("On macOS: brew install git")
        sys.exit(1)
    
    global GIT_PATH, ROOT_PATH
    ROOT_PATH = root_path
    GIT_PATH = os.path.join(ROOT_PATH, "olex2-gui-git")
    
    if not os.path.exists(GIT_PATH):
        print(f"ERROR: Git repository path does not exist: {GIT_PATH}")
        print("Please ensure the olex2-gui-git submodule is initialized")
        sys.exit(1)
    
    os.chdir(GIT_PATH)
    
    # Check if this is a git-svn repository
    if not os.path.exists(os.path.join(GIT_PATH, ".git", "svn")):
        print("WARNING: This does not appear to be a git-svn repository")
        print("Git-SVN metadata (.git/svn) not found")
        print("The repository may need to be initialized with 'git svn init'")
    
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
