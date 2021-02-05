from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPConnection
from urllib.parse import urlparse, parse_qs
import json
import re
import logging
import config

# формат запроса: http://127.0.0.1:5000/api?unit_in=USD&unit_out=RUR&value_in=10.0

# server_address = ('localhost', 5000)

exchange_url = 'www.cbr.ru'
exchange_get = '/currency_base/daily/'
pattern = r'<td>.*</td>\s*<td>(\w*)</td>\s*<td>.*</td>\s*<td>.*</td>\s*<td>([0-9,]*)</td>'

index_page = '''
    <html>
        <head>
            <title>Currency converter</title>
        </head>
        <body>
            <h4>Welcome to the currency converter</h4>
            <p>This app only works through API</p>
            <p>Request example: {}/api?unit_in=USD&unit_out=RUR&value_in=10.0</p>
            <p>Note: One of the units must be 'RUR' or 'RUB'</p>
        </body>
    </html>
'''

log_format='%(asctime)s [%(levelname)s] %(message)s'


def scraping(data, unit):
    matches = re.findall(pattern, data)
    for match in matches:
        if match[0] == unit:
            try:
                return float(match[1].replace(',', '.'))
            except:
                return None
    logger.error(f'Exchange data not found')


def get_exchange_rate(unit='USD'):
    connection = HTTPConnection(exchange_url)
    connection.request('GET', exchange_get)
    response = connection.getresponse()
    if response.status != 200:
        logger.error(f'Exchange server connection error')
        connection.close()
        return None
    data = response.read().decode('utf-8')
    connection.close()
    return scraping(data, unit)


def get_result(unit_in, unit_out, value_in):
    if unit_in in ['RUR', 'RUB']:
        rate = get_exchange_rate(unit_out)
        if rate is None or rate == 0:
            return None
        return value_in / rate
    elif unit_out in ['RUR', 'RUB']:
        rate = get_exchange_rate(unit_in)
        if rate is None:
            return None
        return value_in * rate
    else:
        return None


def compose_json(unit_in, unit_out, value_in):
    value_out = get_result(unit_in, unit_out, value_in)
    if value_out is None:
        return None
    result = {
        'unit_in': unit_in,
        'unit_out': unit_out,
        'value_in': value_in,
        'value_out': value_out
    }
    return result


def compose_json_error(code, message):
    result = {
        'error_code': code,
        'message': message
    }
    if code == 400:
        result['requesr_example'] = '/api?unit_in=USD&unit_out=RUR&value_in=10.5'
    return result


def compose_html(url):
    return index_page.format(url)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f'Request: {self.path}')
        components = urlparse(self.path)
        if components.path == '/' or components.path == '/index':
            self.resp_index()
        elif components.path == '/api':
            query = parse_qs(components.query)
            if 'unit_in' not in query or 'unit_out' not in query or 'unit_in' not in query:
                self.resp_error_json(400)
                return
            try:
                value_in = float(query['value_in'][0])
            except:
                self.resp_error_json(400)
            else:
                self.resp_json(query['unit_in'][0].upper(), query['unit_out'][0].upper(), value_in)
        else:
            self.resp_error(404)

    def resp_index(self):
        logger.info(f'Response: 200 OK')
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(compose_html(f'http://{self.server.server_address[0]}:{self.server.server_address[1]}'), 'utf8'))

    def resp_json(self, unit_in, unit_out, value_in):
        data = compose_json(unit_in, unit_out, value_in)
        if data is None:
            self.resp_error_json(400)
            return
        logger.info(f'Response: 200 OK')
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(data), 'utf8'))

    def resp_error(self, code):
        shortmsg, _ = self.responses[code]
        logger.info(f'Error: {code} {shortmsg}')
        self.send_error(code)

    def resp_error_json(self, code):
        shortmsg, _ = self.responses[code]
        logger.info(f'Error: {code} {shortmsg}')
        self.send_response(code)
        self.send_header('content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(compose_json_error(code, shortmsg)), 'utf8'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename=config.log_filename, format=log_format)
    logger = logging.getLogger('exchange')
    server = HTTPServer(config.server_address, HttpHandler)
    logger.info(f'Start server http://{config.server_address[0]}:{config.server_address[1]}')
    server.serve_forever()
