#!/usr/bin/python

from subprocess import run
import os

os.chdir("/home/lucas/olex2-gui-setup/olex2-gui-git")
run("git svn fetch".split())
run("git push --all".split())
