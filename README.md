# Syncing olex2-svn to olex2-gui
# BORKED
It is not working for now. I have to figure out how to basically do the same thing and keep the authors. For now I am syncing my repo using git svn fetch in my machine and pushing it to remote 
---

This repo is responsible for syncing the olex2-gui with olex2-svn. It is not official and I am not affiliated with OlexSYS. I also have GitHub Actions running every hour to keep it synced.
I don't know why someone would want to use this, but I keep it here because I may use it in the future and it doesn't contain anything that can't be public.

Basically, you have to setup an SVN repository. After that, setup a git repository using the instructions on [convert.md](convert.md). A python script is also provided ([from_subversion.py](from_subversion.py)).

After this you just have to create a file called revision in the root of this repository. That file should contain the last revision. If you don't know it, just put 0 in it. The file is necessary.
