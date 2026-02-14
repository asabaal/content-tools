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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    
    app = create_app()
    app.run(debug=True, host=args.host, port=args.port)
