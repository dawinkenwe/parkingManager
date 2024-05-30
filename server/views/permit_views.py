from flask import Blueprint, current_app, jsonify, render_template, request
from server.cache import cache
from server.helpers import parkingboss_api_helper
from server.helpers.error_handler import ExternalAPIError, ResponseParsingError

# Create a Blueprint for the person-related views
permit_blueprint = Blueprint('permits', __name__, url_prefix='/permits')


# Define a route for /person/hello
@permit_blueprint.route('/hello')
def hello_person():
    return 'Hello, World! This is the permits view.'


@permit_blueprint.route('', methods=['GET'])
@cache.cached(timeout=50)
def list_permits():
    try:
        return render_template("list_permits.html", permits=parkingboss_api_helper.get_permits())
    except (ExternalAPIError, ResponseParsingError) as e:
        return jsonify({'error': e.message}), e.status_code


# TODO: CHECK WITH DURATIONS
@permit_blueprint.route('', methods=['POST'])
def create_permit():
    try:
        form = request.form.to_dict()
        print(form)
        duration = f"PT{form['duration']}H" if form['duration'] and form['duration'].isnumeric() else None
        print(duration)
        parkingboss_api_helper.create_permit(license_plate=form['licenseplate'], duration=duration, email=None, phone=None)
        cache.delete('permits/list_permits')
        return render_template("list_permits.html", permits=parkingboss_api_helper.get_permits())
    except (ExternalAPIError, ResponseParsingError) as e:
        return jsonify({'error': e.message}), e.status_code


# TODO: Fix the page still showing deleted permit for a little bit
# Might be a caching issue, might be better to return a non refresh
# code and have the javascript manually remove the permit from the
# list anyways after clicking the button and receiving the success?
@permit_blueprint.route('/<permit_id>', methods=['DELETE'])
def delete_permit(permit_id):
    try:
        parkingboss_api_helper.delete_permit(permit_id)
        cache.delete('permits/list_permits')
        return jsonify({'permit_id': permit_id}), 200
        return render_template("list_permits.html", permits=parkingboss_api_helper.get_permits())
    except (ExternalAPIError, ResponseParsingError) as e:
        return jsonify({'error': e.message}), e.status_code


@permit_blueprint.route('/create', methods=['GET'])
def render_create_permit_form():
    return render_template('create_permit.html')
