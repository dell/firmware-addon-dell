
import os

def mkselfrelpath(*args):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), *args))

__VERSION__="unreleased version"
LIBEXECDIR=mkselfrelpath("..", "libexec")
