import requests
import datetime
from decimal import Decimal
import os

from flask import current_app, jsonify

from server.helpers.error_handler import ExternalAPIError

# Environment Variables
LOCATION_ID = os.environ.get('LOCATION_ID')
TENANT = os.environ.get('TENANT')
TENANT_PW = os.environ.get('TENANT_PW')
CANCEL_EMAIL = os.environ.get('CANCEL_EMAIL')
MONTHLY_USAGE_QUOTA = os.environ.get('MONTHLY_USAGE_QUOTA')

# API URLS
TOKEN_URL = 'https://api.parkingboss.com/v1/accounts/auth/tokens'
USAGE_URL = f'https://api.parkingboss.com/v1/locations/{LOCATION_ID}'
PERMITS_URL = f'https://api.parkingboss.com/v1/locations/{LOCATION_ID}/tenants'
CREATE_URL = "https://api.parkingboss.com/v1/permits/temporary"


def generate_timestamp_z():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def generate_utc_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-08:00'


def get_tenant_id_and_bearer_token():
    params = {'viewpoint': generate_timestamp_z(), 'location': LOCATION_ID, 'tenant': TENANT, 'password': TENANT_PW}
    current_app.logger.info(f'Calling POST to: {TOKEN_URL} with params: {params}')
    try:
        response = requests.post(TOKEN_URL, params=params, headers={"Content-Type": "application/json"},)
        response.raise_for_status()
        response = response.json()
        return {"tenant_id": response["accounts"]["item"], "bearer": response["token"]}
    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ExternalAPIError() from e


def get_usage_and_policy_id():
    auth_data = get_tenant_id_and_bearer_token()
    params = {"viewpoint": generate_utc_timestamp(), "Authorization": f"bearer {auth_data['bearer']}", "sample": "PT24H"}
    full_url = f"{USAGE_URL}/tenants/{auth_data['tenant_id']}/permits/temporary/usage"
    current_app.logger.info(f'Calling GET to: {full_url} with params: {params}')
    try:
        response = requests.get(full_url, params=params, headers={"Content-Type": "application/json"},)
        response.raise_for_status()
        current_app.logger.info(f'Parking API request succeeded')
        j = response.json()

        # Get current usage
        dic = next(iter(j["usage"]["items"].values()))["used"]
        usage = next(iter(dic.values()))["display"]

        policy_id = next(iter(j["issuers"]["items"].values()))["policy"]
        current_app.logger.info(f'Returning usage: {usage}, policy_id: {policy_id}')
        return {"usage": usage, "policy_id": policy_id}
    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ExternalAPIError() from e


def get_remaining_usage():
    quota = Decimal(str(MONTHLY_USAGE_QUOTA)).quantize(Decimal('0.01'))
    usage = Decimal(str(get_usage_and_policy_id()["usage"])).quantize(Decimal('0.01'))
    return quota - usage


def get_permits():
    auth_data = get_tenant_id_and_bearer_token()
    params = {"sample": "PT24H", "viewpoint": generate_utc_timestamp(), "authorization": f"bearer {auth_data['bearer']}"}
    full_url = f"{PERMITS_URL}/{auth_data['tenant_id']}/permits/temporary/usage"
    permits = []
    try:
        current_app.logger.info(f'Calling GET to: {full_url} with params: {params}')
        response = requests.get(full_url, params=params)
        response.raise_for_status()

        response_permits = response.json()
        for permit_id, permit_dict in response_permits["permits"]["items"].items():
            vehicle_id = permit_dict["vehicle"]
            license_plate = response_permits["vehicles"]["items"][vehicle_id]["display"]
            permit_expiry = permit_dict["lifecycle"]["invalid"]
            permits.append({"license_plate": license_plate, "expiration": permit_expiry, "id": permit_id})

        return permits

    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ExternalAPIError() from e


def create_permit(license_plate, duration, email=None, phone=None):
    policy_id = get_usage_and_policy_id()["policy_id"]
    params = {"viewpoint": generate_timestamp_z(), "location": LOCATION_ID,
              "policy": policy_id, "vehicle": license_plate, "tenant": "1168-A",
              "token": TENANT_PW, "startDate": "", "duration": "PT1H",
              "email": email, "tel": phone}
    form_data = {"location": LOCATION_ID,
                 "policy": policy_id, "vehicle": license_plate, "tenant": "1168-A",
                 "token": TENANT_PW, "startDate": "", "duration": "PT1H",
                 "email": email, "tel": phone}
    permit_id = None

    try:
        # Make a request to the external API
        current_app.logger.info(f'Calling POST to: {CREATE_URL} with params: {params} and data: {form_data}')
        response = requests.post(CREATE_URL,
                                 params=params,
                                 data=form_data
                                 )
        response.raise_for_status()

        dic = response.json()
        return dic["permits"]["item"]

    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ExternalAPIError() from e


def delete_permit(permit_id):
    delete_url = "https://api.parkingboss.com/v1/permits/" + permit_id + "/expires"
    params = {"viewpoint": generate_timestamp_z(), "permit": permit_id, "to": CANCEL_EMAIL}

    try:
        current_app.logger.info(f'Calling PUT to: {delete_url} with params: {params}')
        response = requests.put(delete_url, params=params)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        return jsonify({'error': error_message})

    return False
