import requests
import datetime
import os

# Environment Variables
LOCATION_ID = os.environ.get('LOCATION_ID')
TENANT = os.environ.get('TENANT')
TENANT_PW = os.environ.get('TENANT_PW')

# API URLS
TOKEN_URL = 'https://api.parkingboss.com/v1/accounts/auth/tokens'
USAGE_URL = 'https://api.parkingboss.com/v1/locations'
PERMITS_URL = f'https://api.parkingboss.com/v1/locations/{LOCATION_ID}/tenants'
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
    params = {"viewpoint": generate_timestamp_8(), "Authorization": f"bearer {auth_data['token']}", "sample": "PT24H"}
    response = requests.get(f"{USAGE_URL}/{auth_data['tenant_id']}/permits/temporary/usage",
                            params=params,
                            headers={"Content-Type": "application/json"},
                            )
    j = response.json()

    # Get current usage
    dic = next(iter(j["usage"]["items"].values()))["used"]
    usage = next(iter(dic.values()))["display"]

    policy_id = next(iter(j["issuers"]["items"].values()))["policy"]
    return {"usage": usage, "policy_id": policy_id}


def get_permits():
    auth_data = get_tenant_id_and_bearer_token()
    params = {"sample": "PT24H", "viewpoint": generate_timestamp_8(), "authorization": f"bearer {auth_data["bearer"]}"}
    response = requests.get(f"{PERMITS_URL}/{auth_data['tenant_id']}/permits/temporary/usage")
