import socket


def main():
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    connection, address = server_socket.accept()

    while True:
        message = connection.recv(1024).decode()
        if not message:
            break
        print(f'Received message: {message}')
        msg = input('>>> ')
        connection.send(msg.encode())
    connection.close()
    server_socket.close()


if __name__ == '__main__':
    main()
