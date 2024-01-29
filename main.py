from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import mimetypes
from pathlib import Path
import socket
from threading import Thread
import urllib.parse

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class GoITFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message.html':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    parse_dict = {key: value for key, value in [el.split("=") for el in parse_data.split("&")]}

    username = parse_dict.get('username', '')
    message = parse_dict.get('message', '')

    current_date_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    entry = {current_date_time_str: {"username": username, "message": message}}

    storage_directory = Path('storage')
    storage_directory.mkdir(parents=True, exist_ok=True)

    data_file = storage_directory / 'data.json'

    if not data_file.exists():
        with data_file.open('w', encoding='utf-8') as file:
            json.dump({}, file)

    try:
        with data_file.open('r+', encoding='utf-8') as file:

            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}

            existing_data.update(entry)

            file.seek(0)
            file.truncate()

            json.dump(existing_data, file, ensure_ascii=False, indent=2)

    except ValueError as e:
        logging.error(f"Error parsing data: {e}")
    except OSError as e:
        logging.error(f"Error writing to file: {e}")


def run_socket_server(host, port):
    storage_directory = Path('storage')
    storage_directory.mkdir(parents=True, exist_ok=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info('Starting Socket-server...')
    try:
        while True:
            message, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f'Socket received: {address}: {message}')
            save_data_from_form(message)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoITFramework)
    logging.info('Starting HTTP-server...')
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
