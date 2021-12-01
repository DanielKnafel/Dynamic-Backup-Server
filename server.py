import sys
import socket
import os
import random
import string
import utils as u

class Message:
    cmd = 0x0
    path_len = 0
    data_len = 0
    path = ''

    def __init__(self, cmd, path_len, data_len, path):
        self.cmd = cmd
        self.path_len = path_len
        self.data_len = data_len
        self.path = path
    
    def send_message(self, clientID):
        abs_path = os.path.join(clientID, self.path)
        if self.cmd == u.NEWFI:
            u.send_file(abs_path, self.path)
        elif self.cmd == u.CHNM:

        elif self.cmd == u.MOV:

        elif self.cmd == u.NEWFO:

        elif self.cmd == u.DEL:
            header = u.make_header(u.DEL, self.path_len, self.data_len, self.path)
            u.send(header)

class Client:
    key = ''
    mainDirectory = ''
    # maps IP to update list of messages
    devices = {}

    def __init__(self, key, mainDirectory):
        self.key = key
        self.mainDirectory = mainDirectory

    def add_device(self, clientIPAddress):
        if clientIPAddress not in self.devices.keys:
            self.devices[clientIPAddress] = []
    
    def add_message_to_all(self, currentIP ,message):
        for ip in self.devices:
            if ip != currentIP:
                self.devices[ip].append(message)
    
    def send_messages_to(self, clientSocket ,currentIP):
        for message in self.devices[currentIP]:
            message.send_message(clientSocket)


clients = {}

# New Client Handeling #
def generate_key():
    # generate a random key of length KEY_SIZE
    key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=u.KEY_SIZE))
    return key

def create_main_client_dir(clientKey):
    print(f"creating dir {clientKey}")
    os.mkdir(clientKey)

def handle_new_client(clientIP):
    key = generate_key()
    u.my_socket.send(key.encode())
    create_main_client_dir(key)
    pathLen = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
    print(f"path len is: {pathLen}")
    path = u.my_socket.recv(pathLen)
    print(f"path is: {path.decode()}")
    client = Client(key, path.decode())
    client.addDevice(clientIP)
    clients[key] = client
    return client
 
# Existing Client Handeling #

def handle_existing_client(clientIP):
    key = u.my_socket.recv(u.KEY_SIZE).decode()
    try:
        client = clients[key]
        client.addDevice(clientIP)
        return client
    except:
        print("no such client")


def handle_client(clientIP):
    cmd = u.my_socket.recv(u.COMMAND_SIZE)
    client = None
    if cmd == u.EID: # client has an ID
        client = handle_existing_client(clientIP)
    else:
        client = handle_new_client(clientIP)
    # start reaeding command
    cmd = u.my_socket.recv(u.COMMAND_SIZE)
    path_len = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
    data_len = int.from_bytes(u.my_socket.recv(u.FILE_SIZE), 'big')
    path = u.my_socket.recv(path_len)
    if cmd == u.NEWFI:
        u.create_file(path, data_len, client.key, u.my_socket)
        client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path))
    elif cmd == u.CHNM:
        u.change_name(path, data_len, client.key, u.my_socket)
    elif cmd == u.MOV:
        u.move(path, data_len, client.key, u.my_socket)
    elif cmd == u.NEWFO:
        u.create_folder(path, client.key)
    elif cmd == u.DEL:
        u.delete_dir(os.path.join(client.key, path))
    elif cmd == u.UPD:
        client.send_messages_to(u.my_socket, clientIP)
    elif cmd == u.FIN:
        u.communication_finished(u.my_socket)
    else:
        print(f"invalid cmd -{cmd}-")

def start_server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("", port))
    serverSocket.listen()
    while True:
        print("waiting for client")
        u.my_socket, clientAddress = serverSocket.accept()
        print(f"client {clientAddress} connected")
        handle_client(clientAddress[0])
        print(f"client {clientAddress} dissconnected")

def main():
    if len(sys.argv) < 2:
        print("Not enough args")
        return
    port = int(sys.argv[1])
    start_server(port)

if __name__ == "__main__":
    print("\nServer Active...->")
    main()