import unittest
from mock import Mock, patch
from decimal import Decimal
from requests import RequestException
from server import create_app
from server.helpers import parkingboss_api_helper
from server.helpers.error_handler import ExternalAPIError, ResponseParsingError
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
        self.expected_response = {"tenant_id": self.tenant_id, "bearer": self.token}
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"accounts": {"item": self.tenant_id}, "token": self.token}


    def tearDown(self):
        # Pop the Flask application context after each test
        self.app_context.pop()


    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_success_flow(self, mock_app, mock_timestamp, mock_post):
        mock_post.return_value = self.mock_response
        mock_timestamp.return_value = self.mock_timestamp

        response = parkingboss_api_helper.get_tenant_id_and_bearer_token()

        self.assertEqual(self.expected_response, response)


    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_request_exception_flow(self, mock_app, mock_timestamp, mock_post):
        mock_post.side_effect = RequestException("Test Exception")

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.get_tenant_id_and_bearer_token()
        mock_app.logger.exception.assert_called_once()


    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_key_error_in_response(self, mock_app, mock_timestamp, mock_post):
        self.mock_response.json.return_value = {"asdf": "gg"}
        mock_post.return_value = self.mock_response

        with self.assertRaises(ResponseParsingError):
            response = parkingboss_api_helper.get_tenant_id_and_bearer_token()
        mock_app.logger.exception.assert_called_once()


class TestGetUsageAndPolicyID(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "12345"
        self.tenant = "tenant"
        self.location = "LOCATION"
        self.tenant_pw = "TENANT_PW"
        self.mock_timestamp = "now"
        self.mock_bearer = "bearer_token"
        self.policy_id = "policy_id"
        self.usage = "123"
        parkingboss_api_helper.LOCATION_ID = self.location
        parkingboss_api_helper.TENANT = self.tenant
        parkingboss_api_helper.TENANT_PW = self.tenant_pw
        self.mock_auth_data = {"bearer": self.mock_bearer, "tenant_id": self.tenant_id}
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"usage": {"items": {"item_id": {"used": {"item_id2": {"display": self.usage}}}}}, "issuers": {"items": {"item_id": {"policy": self.policy_id}}}}
        self.expected_response = {"usage": self.usage, "policy_id": self.policy_id}

        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Pop the Flask application context after each test
        self.app_context.pop()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_success_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.return_value = self.mock_response

        response = parkingboss_api_helper.get_usage_and_policy_id()

        self.assertEqual(self.expected_response, response)

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_get_tenant_id_exception_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.side_effect = ExternalAPIError("message")
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.return_value = self.mock_response

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.get_usage_and_policy_id()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_requests_exception_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.side_effect = RequestException("Test Exception")

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.get_usage_and_policy_id()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_key_error_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        self.mock_response.json.return_value = {"mocked": "response"}
        mock_get.return_value = self.mock_response

        with self.assertRaises(ResponseParsingError):
            response = parkingboss_api_helper.get_usage_and_policy_id()

class TestGetRemainingUsage(unittest.TestCase):
    def setUp(self):
        pass

    @patch('server.helpers.parkingboss_api_helper.get_usage_and_policy_id')
    def test_decimal_usage(self, mock_usage):
        mock_usage.return_value = {"usage": 79.92, "policy_id": "other_value"}
        parkingboss_api_helper.MONTHLY_USAGE_QUOTA = 100
        expected_value = Decimal("20.08")
        value = parkingboss_api_helper.get_remaining_usage()
        self.assertEqual(expected_value, value)


class TestGetPermits(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "12345"
        self.tenant = "tenant"
        self.location = "LOCATION"
        self.tenant_pw = "TENANT_PW"
        self.mock_timestamp = "now"
        self.mock_bearer = "bearer_token"
        self.policy_id = "policy_id"
        self.usage = "123"
        parkingboss_api_helper.LOCATION_ID = self.location
        parkingboss_api_helper.TENANT = self.tenant
        parkingboss_api_helper.TENANT_PW = self.tenant_pw
        self.mock_auth_data = {"bearer": self.mock_bearer, "tenant_id": self.tenant_id}
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"permits": {"items": {"permit_id1": {"vehicle": "vehicle_id1", "lifecycle": {"invalid": "permit_expiry1"}}, "permit_id2": {"vehicle": "vehicle_id2", "lifecycle": {"invalid": "permit_expiry2"}}}}, "vehicles": {"items": {"vehicle_id1": {"display": "license_plate1"}, "vehicle_id2": {"display": "license_plate2"}}}}
        self.expected_response = [{"license_plate": "license_plate1", "expiration": "permit_expiry1", "id": "permit_id1"}, {"license_plate": "license_plate2", "expiration": "permit_expiry2", "id": "permit_id2"}]

        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_success_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.return_value = self.mock_response

        expected_params = {"sample": "PT24H", "viewpoint": self.mock_timestamp, "Authorization": f"bearer {self.mock_bearer}"}
        expected_full_url = f"{parkingboss_api_helper.PERMITS_URL}/{self.tenant_id}/permits/temporary/usage"

        response = parkingboss_api_helper.get_permits()
        mock_get.assert_called_once_with(expected_full_url, params=expected_params)

        self.assertEqual(self.expected_response, response)

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_get_tenant_id_exception_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.side_effect = ExternalAPIError("message")
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.return_value = self.mock_response

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.get_permits()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_requests_exception_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.side_effect = RequestException("Test Exception")

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.get_permits()

    @patch('server.helpers.parkingboss_api_helper.get_tenant_id_and_bearer_token')
    @patch('server.helpers.parkingboss_api_helper.generate_utc_timestamp')
    @patch('server.helpers.parkingboss_api_helper.requests.get')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_key_error_flow(self, mock_app, mock_get, mock_timestamp, mock_get_tenant_id):
        mock_get_tenant_id.return_value = self.mock_auth_data
        mock_timestamp.return_value = self.mock_timestamp
        self.mock_response.json.return_value = {"mocked": "response"}
        mock_get.return_value = self.mock_response

        with self.assertRaises(ResponseParsingError):
            response = parkingboss_api_helper.get_permits()


class TestCreatePermit(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "12345"
        self.tenant = "tenant"
        self.location = "LOCATION"
        self.tenant_pw = "TENANT_PW"
        self.mock_timestamp = "now"
        self.mock_bearer = "bearer_token"
        self.policy_id = "policy_id"
        self.usage = "123"
        self.license_plate = "license_plate"
        self.duration = "PT1H"
        parkingboss_api_helper.LOCATION_ID = self.location
        parkingboss_api_helper.TENANT = self.tenant
        parkingboss_api_helper.TENANT_PW = self.tenant_pw
        self.mock_get_usage = {"usage": self.usage, "policy_id": self.policy_id}
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"permits": {"item": "returned_permit_id"}}
        self.expected_response = "returned_permit_id"
        self.expected_params = {"viewpoint": self.mock_timestamp, "location": self.location,
                                "policy": self.policy_id, "vehicle": self.license_plate, "tenant": self.tenant,
                                "token": self.tenant_pw, "startDate": "", "duration": "PT1H",
                                "email": None, "tel": None}
        self.expected_form_data = {"location": self.location,
                                   "policy": self.policy_id, "vehicle": self.license_plate, "tenant": self.tenant,
                                   "token": self.tenant_pw, "startDate": "", "duration": self.duration,
                                   "email": None, "tel": None}

        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    @patch('server.helpers.parkingboss_api_helper.get_usage_and_policy_id')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_success_flow(self, mock_app, mock_post, mock_timestamp, mock_get_usage):
        mock_get_usage.return_value = self.mock_get_usage
        mock_timestamp.return_value = self.mock_timestamp
        mock_post.return_value = self.mock_response

        expected_params = {"sample": "PT24H", "viewpoint": self.mock_timestamp, "Authorization": f"bearer {self.mock_bearer}"}
        expected_full_url = f"{parkingboss_api_helper.CREATE_URL}"
        response = parkingboss_api_helper.create_permit(license_plate=self.license_plate)
        mock_post.assert_called_once_with(expected_full_url, params=self.expected_params, data=self.expected_form_data)

        self.assertEqual(self.expected_response, response)


    @patch('server.helpers.parkingboss_api_helper.get_usage_and_policy_id')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_requests_exception_flow(self, mock_app, mock_get, mock_timestamp, mock_get_usage):
        mock_get_usage.return_value = self.mock_get_usage
        mock_timestamp.return_value = self.mock_timestamp
        mock_get.side_effect = RequestException("Test Exception")

        with self.assertRaises(ExternalAPIError):
            response = parkingboss_api_helper.create_permit(license_plate=self.license_plate)

    @patch('server.helpers.parkingboss_api_helper.get_usage_and_policy_id')
    @patch('server.helpers.parkingboss_api_helper.generate_timestamp_z')
    @patch('server.helpers.parkingboss_api_helper.requests.post')
    @patch('server.helpers.parkingboss_api_helper.current_app')
    def test_key_error_flow(self, mock_app, mock_get, mock_timestamp, mock_get_usage):
        mock_get_usage.return_value = self.mock_get_usage
        mock_timestamp.return_value = self.mock_timestamp
        self.mock_response.json.return_value = {"mocked": "response"}
        mock_get.return_value = self.mock_response

        with self.assertRaises(ResponseParsingError):
            response = parkingboss_api_helper.create_permit(license_plate=self.license_plate)


if __name__ == '__main__':
    unittest.main()
