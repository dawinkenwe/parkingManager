from flask import Blueprint, current_app, render_template
from server.cache import cache
from server.helpers.parkingboss_api_helper import get_permits as parking_api_permits

# Create a Blueprint for the person-related views
permit_blueprint = Blueprint('permits', __name__, url_prefix='/permits')


# Define a route for /person/hello
@permit_blueprint.route('/hello')
def hello_person():
    return 'Hello, World! This is the permits view.'


@permit_blueprint.route('/get')
@cache.cached(timeout=50)
def get_permits():
    return render_template("list_permits.html", permits=parking_api_permits())
