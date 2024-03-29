import unittest
from mock import Mock, patch
from server import create_app
from server.helpers import parkingboss_api_helper
from flask import Flask


class TestGetTenantIdAndBearerToken(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "12345"
        self.token = "thisismyauthtoken"
        self.tenant = "tenant"
        self.location = "LOCATION"
        self.tenant_pw = "TENANT_PW"
        self.mock_timestamp = "now"
        parkingboss_api_helper.LOCATION_ID = self.location
        parkingboss_api_helper.TENANT = self.tenant
        parkingboss_api_helper.TENANT_PW = self.tenant_pw
        self.expected_params = {'viewpoint': self.mock_timestamp, 'location': self.location, 'tenant': self.tenant, 'password': self.tenant_pw}
        self.mock_request_response = {"accounts": {"item": self.tenant_id}, "token": self.token}
        self.expected_response = {"tenant_id": self.tenant_id, "bearer": self.token}
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Pop the Flask application context after each test
        self.app_context.pop()


    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_success_flow(self, mock_app, mock_timestamp, mock_post):
        # Create mock response JSON
        mock_response = Mock()
        mock_response.json.return_value = self.mock_request_response

        # Set POST request to return Mock
        mock_post.return_value = mock_response
        mock_timestamp.return_value = self.mock_timestamp

        response = parkingboss_api_helper.get_tenant_id_and_bearer_token()

        self.assertEqual(self.expected_response, response)


    def test_request_exception_flow(self, mock_app, mock_timestamp, mock_post):


"""
    def get_tenant_id_and_bearer_token():
        params = {'viewpoint': generate_timestamp_z(), 'location': LOCATION_ID, 'tenant': TENANT, 'password': TENANT_PW}
        current_app.logger.info(f'Calling POST to: {TOKEN_URL} with params: {params}')
        try:
            response = requests.post(TOKEN_URL, params=params, headers={"Content-Type": "application/json"}, ).json()
            response.raise_for_status()
            return {"tenant_id": response["accounts"]["item"], "bearer": response["token"]}
        except requests.RequestException as e:
            current_app.logger.exception('Error with API request: %s', str(e))
            raise ExternalAPIError() from e
        except KeyError as e:
            current_app.logger.exception('Malformatted API response: %s', str(e))
            raise ExternalAPIError() from e
"""

if __name__ == '__main__':
    unittest.main()
