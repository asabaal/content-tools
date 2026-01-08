import os
from flask import Flask


def create_app():
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = 'dev-key-for-testing'
    
    from . import routes
    routes.init_routes(app)
    
    return app
