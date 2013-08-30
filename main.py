"""
Initialize Flask app
"""

import boot
boot.setup()

from ripl import create_app


app = create_app()

