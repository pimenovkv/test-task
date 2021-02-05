import unittest
from http.client import HTTPConnection
import json
import config


class Tests(unittest.TestCase):
    def setUp(self):
        self.connection = HTTPConnection(f'{config.server_address[0]}:{config.server_address[1]}')

    def tearDown(self):
        self.connection.close()

    def test_index(self):
        url = '/index'
        self.connection.request('GET', url)
        self.response = self.connection.getresponse()
        self.assertEqual(self.response.status, 200)
        content_type = self.response.headers.get_content_type()
        self.assertEqual(content_type, 'text/html')

    def test_api_400(self):
        url = '/api'
        self.connection.request('GET', url)
        self.response = self.connection.getresponse()
        self.assertEqual(self.response.status, 400)

    def test_api_base(self, url='/api?unit_in=USD&unit_out=RUR&value_in=10.0', status=200):
        self.connection.request('GET', url)
        self.response = self.connection.getresponse()
        self.assertEqual(self.response.status, status)
        content_type = self.response.headers.get_content_type()
        self.assertEqual(content_type, 'application/json')

    def test_api_ok_RUR(self):
        url = '/api?unit_in=USD&unit_out=RUR&value_in=10.0'
        self.test_api_base(url)
        data = json.loads(self.response.read())
        ref_data = {'unit_in': 'USD', 'unit_out': 'RUR', 'value_in': 10.0, 'value_out': 0.0}
        self.assertEqual(data['unit_in'], ref_data['unit_in'])
        self.assertEqual(data['unit_out'], ref_data['unit_out'])
        self.assertEqual(data['value_in'], ref_data['value_in'])
        self.assertGreater(data['value_out'], ref_data['value_out'])

    def test_api_ok_RUB(self):
        url = '/api?unit_in=RUB&unit_out=USD&value_in=10.0'
        self.test_api_base(url)
        data = json.loads(self.response.read())
        ref_data = {'unit_in': 'RUB', 'unit_out': 'USD', 'value_in': 10.0, 'value_out': 0.0}
        self.assertEqual(data['unit_in'], ref_data['unit_in'])
        self.assertEqual(data['unit_out'], ref_data['unit_out'])
        self.assertEqual(data['value_in'], ref_data['value_in'])
        self.assertGreater(data['value_out'], ref_data['value_out'])

    def test_api_ok_EUR(self):
        url = '/api?unit_in=RUR&unit_out=EUR&value_in=10.0'
        self.test_api_base(url)
        data = json.loads(self.response.read())
        ref_data = {'unit_in': 'RUR', 'unit_out': 'EUR', 'value_in': 10.0, 'value_out': 0.0}
        self.assertEqual(data['unit_in'], ref_data['unit_in'])
        self.assertEqual(data['unit_out'], ref_data['unit_out'])
        self.assertEqual(data['value_in'], ref_data['value_in'])
        self.assertGreater(data['value_out'], ref_data['value_out'])

    def test_api_error_coma(self):
        url = '/api?unit_in=USD&unit_out=RUR&value_in=10,0'
        self.test_api_base(url, 400)
        data = json.loads(self.response.read())
        ref_data = {"error_code": 400, "message": "Bad Request", "requesr_example": "/api?unit_in=USD&unit_out=RUR&value_in=10.5"}
        self.assertDictEqual(data, ref_data)

    def test_api_error_unit(self):
        url = '/api?unit_in=USD&unit_out=RUZ&value_in=10.0'
        self.test_api_base(url, 400)
        data = json.loads(self.response.read())
        ref_data = {"error_code": 400, "message": "Bad Request", "requesr_example": "/api?unit_in=USD&unit_out=RUR&value_in=10.5"}
        self.assertDictEqual(data, ref_data)


if __name__ == '__main__':
    unittest.main()
