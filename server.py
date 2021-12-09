import sys
import socket
import os
import random
import string
import utils as u
from utils import Message


class Client:
    key = ''
    mainDirectory = ''
    # maps IP to a list of Messages
    devices = {}

    def __init__(self, key, mainDirectory):
        self.key = key
        self.mainDirectory = mainDirectory

    # adds a new PC to the map
    def add_device(self, clientIPAddress):
        if clientIPAddress not in self.devices:
            self.devices[clientIPAddress] = []

    # appends a new message to all other client's PCs (except the one which initiated the change)
    def add_message_to_all(self, currentIP, message):
        for ip in self.devices:
            if ip != currentIP:
                self.devices[ip].append(message)

    # used if the Client connects from a new PC with a key
    def send_main_directory(self):
        u.send(len(self.mainDirectory).to_bytes(u.PATH_LEN_SIZE, 'big'))
        u.send(self.mainDirectory.encode())
        abs_path = os.path.join(self.key, self.mainDirectory)
        u.send_folder(u.my_socket, abs_path, self.mainDirectory)

    # sends all the messages relevant to the specified PC, and clears the list afterwards.
    def send_messages_to(self, clientIPAddress):
        for message in self.devices[clientIPAddress]:
            message.send_message(self.key)
        self.clear_messages(clientIPAddress)

    def clear_messages(self, clientIPAddress):
        self.devices[clientIPAddress].clear()


# global clients map. maps ID to Client object
clients = {}


# New Client Handeling #
def generate_key():
    # generate a random key of length KEY_SIZE
    key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=u.KEY_SIZE))
    return key


# creates the main client folder nested under its ID
def create_main_client_dir(client_key, main_folder):
    os.makedirs(os.path.join(client_key, main_folder))


def handle_new_client(clientIP, path):
    # print("client has no ID")
    # generate a uniqe key
    key = generate_key()
    print(key)
    # inform the client with his new key
    u.my_socket.send(key.encode())
    create_main_client_dir(key, path)
    # add client to the clients map
    client = Client(key, path)
    client.add_device(clientIP)
    clients[key] = client


# Existing Client Handeling #

def handle_existing_client(clientIP, key):
    # print("client has an ID")
    try:
        client = clients[key]
        client.add_device(clientIP)

        client.send_main_directory()
        u.send(u.FIN)
    except Exception as e:  # no such client
        pass
        # print(e)
        # print("no such client")


# read the protocol header
def readHeader():
    key = u.my_socket.recv(u.KEY_SIZE).decode()
    path_len = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
    data_len = int.from_bytes(u.my_socket.recv(u.FILE_SIZE), 'big')
    path = u.my_socket.recv(path_len).decode()
    return key, path_len, data_len, path


# start reading commands
def handle_client(clientIP):
    cmd = u.my_socket.recv(u.COMMAND_SIZE)

    while cmd != b'':
        key, path_len, data_len, path = readHeader()
        # print(f"got: \t key: {key}\n\t cmd: {cmd} \n\t path: {path} \n\t from {clientIP}")
        if cmd == u.EID:  # client has an ID
            handle_existing_client(clientIP, key)
            return
        elif cmd == u.NID:  # client has no ID
            handle_new_client(clientIP, path)
        else:
            client = None
            try:
                client = clients[key]
            except:
                return  # no such client

            if cmd == u.NEWFI:  # new file
                u.create_file(u.my_socket, path, data_len, client.key)
                client.add_message_to_all(clientIP, Message(cmd, path_len, data_len, path))
            elif cmd == u.NEWFO:  # new folder
                u.create_folder(path, client.key)
                client.add_message_to_all(clientIP, Message(cmd, path_len, data_len, path))
            elif cmd == u.DEL:  # remove directory
                abs_path = os.path.join(client.key, path)
                u.delete_dir(abs_path)
                client.add_message_to_all(clientIP, Message(cmd, path_len, data_len, path))
            elif cmd == u.UPDT:  # send updates
                client.send_messages_to(clientIP)
                u.send(u.FIN)
                return
            else:
                pass  # invalid cmd
        cmd = u.my_socket.recv(u.COMMAND_SIZE)


def start_server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("", port))
    serverSocket.listen(10)
    while True:
        # print("waiting for client")
        u.my_socket, clientAddress = serverSocket.accept()
        # print(f"client {clientAddress} connected")
        clientIP = clientAddress[0]
        handle_client(clientIP)
        # print(f"client {clientAddress} dissconnected")
        u.close()


def main():
    if len(sys.argv) < 2:
        # print("Not enough args")
        return
    port = int(sys.argv[1])
    start_server(port)


if __name__ == "__main__":
    # print("\nServer Active...->")
    main()