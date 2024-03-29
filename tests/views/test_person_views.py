import unittest
from server import create_app

class TestPersonViews(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_hello_person(self):
        response = self.client.get('/person/hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'Hello, World! This is the person view.')

if __name__ == '__main__':
    unittest.main()
