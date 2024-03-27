import requests
import datetime
import os

from flask import jsonify

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


def generate_timestamp_8():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-08:00'


def get_tenant_id_and_bearer_token():
    params = {'viewpoint': generate_timestamp_z(), 'location': LOCATION_ID, 'tenant': TENANT, 'password': TENANT_PW}
    response = requests.post(TOKEN_URL, params=params, headers={"Content-Type": "application/json"},).json()
    return {"tenant_id": response["accounts"]["item"], "bearer": response["token"]}


def get_usage_and_policy_id():

    auth_data = get_tenant_id_and_bearer_token()
    params = {"viewpoint": generate_timestamp_8(), "Authorization": f"bearer {auth_data['bearer']}", "sample": "PT24H"}
    full_url = f"{USAGE_URL}/{auth_data['tenant_id']}/permits/temporary/usage"

    try:

        response = requests.get(f"{USAGE_URL}/{auth_data['tenant_id']}/permits/temporary/usage",
                                params=params,
                                headers={"Content-Type": "application/json"},
                            )
        if response.status_code == 200:
            j = response.json()

            # Get current usage
            dic = next(iter(j["usage"]["items"].values()))["used"]
            usage = next(iter(dic.values()))["display"]

            policy_id = next(iter(j["issuers"]["items"].values()))["policy"]
            return {"usage": usage, "policy_id": policy_id}
        else:
            # If the request was not successful, raise an exception
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle network errors or any other exceptions raised during the request
        error_message = str(e)
        return jsonify({'error': error_message})

    return jsonify({'error': "this shouldn't have happened..."})


def get_remaining_usage():
    return int(MONTHLY_USAGE_QUOTA) - int(get_usage_and_policy_id()["usage"])


def get_permits():
    auth_data = get_tenant_id_and_bearer_token()
    params = {"sample": "PT24H", "viewpoint": generate_timestamp_8(), "authorization": f"bearer {auth_data['bearer']}"}
    retval = []
    try:
        response = requests.get(f"{PERMITS_URL}/{auth_data['tenant_id']}/permits/temporary/usage")

        if response.status_code == 200:
            permits = response.json()
            for permit_id, permit_dict in permits["permits"]["items"].items():
                vehicle_id = permit_dict["vehicle"]
                license_plate = permits["vehicles"]["items"][vehicle_id]["display"]
                permit_expiry = permit_dict["lifecycle"]["invalid"]
                retval.append({"license_plate": license_plate, "expiration": permit_expiry, "id": permit_id})
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle network errors or any other exceptions raised during the request
        error_message = str(e)
        return jsonify({'error': error_message})
    return retval


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
        response = requests.post(CREATE_URL,
                                 params=params,
                                 data=form_data
                                 )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            dic = response.json()
            permit_id = dic["permits"]["item"]
        else:
            # If the request was not successful, raise an exception
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle network errors or any other exceptions raised during the request
        error_message = str(e)
        return jsonify({'error': error_message}), 500

    return permit_id


def delete_permit(permit_id):
    delete_url = "https://api.parkingboss.com/v1/permits/" + permit_id + "/expires"
    params = {"viewpoint": generate_timestamp_z(), "permit": permit_id, "to": CANCEL_EMAIL}

    try:
        response = requests.put(delete_url, params=params)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        return jsonify({'error': error_message})

    return False
