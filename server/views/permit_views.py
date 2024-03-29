from flask import Blueprint, current_app, jsonify, render_template
from server.cache import cache
from server.helpers.parkingboss_api_helper import get_permits as parking_api_permits
from server.helpers.error_handler import ExternalAPIError

# Create a Blueprint for the person-related views
permit_blueprint = Blueprint('permits', __name__, url_prefix='/permits')


# Define a route for /person/hello
@permit_blueprint.route('/hello')
def hello_person():
    return 'Hello, World! This is the permits view.'


@permit_blueprint.route('/get')
@cache.cached(timeout=50)
def get_permits():
    try:
        permits = parking_api_permits()
        return render_template("list_permits.html", permits=parking_api_permits())
    except ExternalAPIError as e:
        return jsonify({'error': e.message}), e.status_code
