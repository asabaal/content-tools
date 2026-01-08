import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from web_app import routes


def create_app():
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = 'dev-key-for-testing'
    routes.init_routes(app)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
