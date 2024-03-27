from flask import Blueprint

# Create a Blueprint for the person-related views
person_blueprint = Blueprint('person', __name__, url_prefix='/person')


# Define a route for /person/hello
@person_blueprint.route('/hello')
def hello_person():
    return 'Hello, World! This is the person view.'


@person_blueprint.route('/get')
def get_people():
    return 'GET DATA RETURNED HERE'