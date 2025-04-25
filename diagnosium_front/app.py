import os
import sys

# Use absolute import for create_app (assuming it's in __init__.py)
from __init__ import create_app
# If you were importing db directly here, it would be:
# from . import db
# If you were importing models directly:
# from . import models

app = create_app()

if __name__ == '__main__':
    # The host='0.0.0.0' makes it accessible from your network
    # The default port is 5000
    app.run(debug=True, host='0.0.0.0')