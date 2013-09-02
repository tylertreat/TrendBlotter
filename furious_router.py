"""Setup path and expose Furious webapp handler."""

import os
import sys


def setup_lib_path():
    """Add lib to path."""

    libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
    if libs_dir not in sys.path:
        sys.path.insert(0, libs_dir)

    libs_externals_dir = os.path.join(libs_dir, 'external')
    if libs_externals_dir not in sys.path:
        sys.path.insert(0, libs_externals_dir)

setup_lib_path()


from furious.handlers import webapp

app = webapp.app

