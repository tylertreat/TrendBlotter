"""Initialize Flask app."""

import furious_router
furious_router.setup_lib_path()

from ripl import create_app


app = create_app()

