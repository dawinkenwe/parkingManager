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


# TODO: This was returning a LOT of permits for some reason. Maybe including expired? Investigate on PB api level
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
        duration = f"PT{request.form['duration']}H" if request.form['duration'] and request.form.duration.isnumeric() else None
        parkingboss_api_helper.create_permit(license_plate=request.form['licenseplate'], duration=duration, email=None, phone=None)
        cache.delete('permit_blueprint/list_permits')
        return render_template("list_permits.html", permits=parkingboss_api_helper.get_permits())
    except (ExternalAPIError, ResponseParsingError) as e:
        return jsonify({'error': e.message}), e.status_code


@permit_blueprint.route('/<permit_id>', methods=['DELETE'])
def delete_permit(permit_id):
    try:
        parkingboss_api_helper.delete_permit(permit_id)
        cache.delete('permit_blueprint/list_permits')
        return render_template("list_permits.html", permits=parkingboss_api_helper.get_permits())
    except (ExternalAPIError, ResponseParsingError) as e:
        return jsonify({'error': e.message}), e.status_code


@permit_blueprint.route('/create', methods=['GET'])
def render_create_permit_form():
    return render_template('create_permit.html')
