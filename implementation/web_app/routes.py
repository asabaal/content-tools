from flask import render_template
from . import views


def init_routes(app):
    @app.route('/')
    def index():
        data = views.get_transcript_data()
        return render_template('index.html', data=data)
