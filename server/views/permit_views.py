from flask import Blueprint, current_app
from server.cache import cache

# Create a Blueprint for the person-related views
permit_blueprint = Blueprint('permits', __name__, url_prefix='/permits')


# Define a route for /person/hello
@permit_blueprint.route('/hello')
def hello_person():
    return 'Hello, World! This is the permits view.'


@permit_blueprint.route('/get')
@cache.cached(timeout=50)
def get_permits():
    return 'GET DATA RETURNED HERE'
