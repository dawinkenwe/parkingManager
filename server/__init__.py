from dotenv import load_dotenv
from typing import Any

from flask import Flask, render_template, Response
from flask_caching import Cache

from .helpers.parkingboss_api_helper import get_remaining_usage
from .models.database import db, init_app
from .cache import cache


def create_app():
    app = Flask(__name__)

    app.config.from_object('config')

    # Initialize the database
    init_app(app)

    # Initialize cache
    cache.init_app(app)

    # Import and register blueprints
    from .views.permit_views import permit_blueprint
    app.register_blueprint(permit_blueprint)
    from .views.person_views import person_blueprint
    app.register_blueprint(person_blueprint)

    # Landing Page
    @app.route("/")
    def home():
        return render_template("home.html", usage=get_remaining_usage())

    # Customize your error pages
    @app.errorhandler(404)
    def unrecognized_object(error: Any) -> Response:
        return Response("404 Not Found", status=404)

    # Prevent Caching
    @app.after_request
    def set_response_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    load_dotenv()

    return app
