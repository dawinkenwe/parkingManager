import requests
import datetime
from dateutil import tz
from decimal import Decimal
import os

from flask import current_app, jsonify

from server.helpers.error_handler import ExternalAPIError, ResponseParsingError

# Environment Variables
LOCATION_ID = os.environ.get('LOCATION_ID')
TENANT = os.environ.get('TENANT')
TENANT_PW = os.environ.get('TENANT_PW')
CANCEL_EMAIL = os.environ.get('CANCEL_EMAIL')
MONTHLY_USAGE_QUOTA = os.environ.get('MONTHLY_USAGE_QUOTA')
TIMEZONE = os.environ.get('TIMEZONE')

# API URLS
TOKEN_URL = 'https://api.parkingboss.com/v1/accounts/auth/tokens'
USAGE_URL = f'https://api.parkingboss.com/v1/locations/{LOCATION_ID}'
PERMITS_URL = f'https://api.parkingboss.com/v1/locations/{LOCATION_ID}/tenants'
CREATE_URL = "https://api.parkingboss.com/v1/permits/temporary"


# Learning - Z is for Zulu time, which is UTC time.
def generate_timestamp_z():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def generate_timestamp_with_utc_offset():
    timestamp = datetime.datetime.now(tz=tz.gettz(TIMEZONE))
    timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return timestamp_str[:-8] + '-' + timestamp_str[-3] + ':' + timestamp_str[-2:]
    return datetime.datetime.now(tz=tz.gettz(TIMEZONE)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-08:00'


def generate_timestamp_with_utc_offset_range_1_month():
    my_tz = tz.gettz(TIMEZONE)
    start = datetime.datetime.now(tz=my_tz)
    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    end = start + datetime.timedelta(days=30)
    start = start.strftime(fmt)
    end = end.strftime(fmt)
    start = start[:-8] + '-' + start[-3] + ':' + start[-2:]
    end = end[:-8] + '-' + end[-3] + ':' + end[-2:]
    return start + '/' + end


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
        raise ResponseParsingError() from e


def get_usage_and_policy_id():
    auth_data = get_tenant_id_and_bearer_token()
    params = {"viewpoint": generate_timestamp_with_utc_offset(), "Authorization": f"bearer {auth_data['bearer']}", "sample": "PT24H"}
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
        return {"usage": usage.split(' ')[0], "policy_id": policy_id}
    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ResponseParsingError() from e
    except IndexError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ResponseParsingError() from e

def get_remaining_usage():
    quota = Decimal(str(MONTHLY_USAGE_QUOTA)).quantize(Decimal('0.01'))
    usage = 0
    usage_dict = None
    try:
        usage_dict = get_usage_and_policy_id()
    except ExternalAPIError as e:
        current_app.logger.exception('Error with API request: %s', str(e))
    except ResponseParsingError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
    if usage_dict is not None and 'usage' in usage_dict and usage_dict["usage"] is not None:
        usage = Decimal(str(usage_dict["usage"])).quantize(Decimal('0.01'))
    return str(quota - usage)


# TODO: CHECK HERE TO SEE IF EXPIRED PERMITS SHOW
# THIS COULD BE CAUSING THE ISSUE WITH THE DELETED PERMITS STILL SHOWING FOR A LITTLE.
def get_permits():
    auth_data = get_tenant_id_and_bearer_token()
    params = {
        "valid": generate_timestamp_with_utc_offset_range_1_month(),
        "viewpoint": generate_timestamp_with_utc_offset(),
        "Authorization": f"bearer {auth_data['bearer']}"
    }
    full_url = f"{PERMITS_URL}/{auth_data['tenant_id']}/permits"
    permits = []
    try:
        current_app.logger.info(f'Calling GET to: {full_url} with params: {params}')
        response = requests.get(full_url, params=params)
        response.raise_for_status()

        response_permits = response.json()
        current_app.logger.info('Got response: %s', str(response_permits))
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
        raise ResponseParsingError() from e


def create_permit(license_plate, duration="PT1H", email=None, phone=None):
    policy_id = get_usage_and_policy_id()["policy_id"]
    params = {"viewpoint": generate_timestamp_z(), "location": LOCATION_ID,
              "policy": policy_id, "vehicle": license_plate, "tenant": TENANT,
              "token": TENANT_PW, "startDate": "", "duration": "PT1H",
              "email": email, "tel": phone}
    form_data = {"location": LOCATION_ID,
                 "policy": policy_id, "vehicle": license_plate, "tenant": TENANT,
                 "token": TENANT_PW, "startDate": "", "duration": duration,
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
        raise ResponseParsingError() from e


def delete_permit(permit_id):
    delete_url = "https://api.parkingboss.com/v1/permits/" + permit_id + "/expires"
    params = {"viewpoint": generate_timestamp_z(), "permit": permit_id, "to": CANCEL_EMAIL, "_method": "PUT"}

    try:
        current_app.logger.info(f'Calling PUT to: {delete_url} with params: {params}')
        response = requests.put(delete_url, params=params)
        response.raise_for_status()
        return {"success": True, "permit_id": permit_id}
    except requests.RequestException as e:
        current_app.logger.exception('Error with API request: %s', str(e))
        raise ExternalAPIError() from e
    except KeyError as e:
        current_app.logger.exception('Malformatted API response: %s', str(e))
        raise ResponseParsingError() from e

