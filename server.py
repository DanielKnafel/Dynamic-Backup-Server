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
    data = ''

    def __init__(self, cmd, path_len, data_len, path, data = ''):
        self.cmd = cmd
        self.path_len = path_len
        self.data_len = data_len
        self.path = path
        self.data = data
    
    def send_message(self, clientID):
        abs_path = os.path.join(clientID, self.path)
        if self.cmd == u.NEWFI:
            u.send_file(abs_path, self.path)
        elif self.cmd == u.CHNM:
            pass
        elif self.cmd == u.MOV:
            header = u.make_header(u.MOV, self.path_len, self.data_len, self.path, '')
            u.send(header)
            u.send(self.data)
        elif self.cmd == u.NEWFO:
            u.send_folder(abs_path, self.path)
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
        if clientIPAddress not in self.devices:
            self.devices[clientIPAddress] = []
    
    def add_message_to_all(self, currentIP ,message):
        for ip in self.devices:
            if ip != currentIP:
                self.devices[ip].append(message)
    
    def send_messages_to(self, clientSocket ,clientIPAddress):
        for message in self.devices[clientIPAddress]:
            message.send_message(clientSocket)
    
    def clear_messages(self, clientIPAddress):
        self.devices[clientIPAddress].clear()

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
    print("client has no ID")
    key = generate_key()
    u.my_socket.send(key.encode())
    create_main_client_dir(key)
    pathLen = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
    print(f"path len is: {pathLen}")
    data_len = u.my_socket.recv(u.FILE_SIZE)
    path = u.my_socket.recv(pathLen)
    print(f"path is: {path.decode()}")
    client = Client(key, path.decode())
    client.add_device(clientIP)
    clients[key] = client
    return client
 
# Existing Client Handeling #

def handle_existing_client(clientIP):
    print("client has an ID")
    key = u.my_socket.recv(u.KEY_SIZE).decode()
    try:
        client = clients[key]
        client.addDevice(clientIP)
        return client
    except:
        print("no such client")

# start reading commands
def handle_client(clientIP, client):
    cmd = 0
    while cmd != u.FIN:
        cmd = u.my_socket.recv(u.COMMAND_SIZE)
        path_len = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
        data_len = int.from_bytes(u.my_socket.recv(u.FILE_SIZE), 'big')
        path = u.my_socket.recv(path_len).decode()
        if cmd == u.NEWFI:
            u.create_file(path, data_len, client.key, u.my_socket)
            client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path))
        elif cmd == u.CHNM:
            u.change_name(path, data_len, client.key, u.my_socket)
            client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path))
        elif cmd == u.MOV:
            # returns the dst path
            dst_path = u.move(path, data_len, client.key, u.my_socket)
            client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path, dst_path))
        elif cmd == u.NEWFO:
            u.create_folder(path, client.key)
            client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path))
        elif cmd == u.DEL:
            if (u.delete_dir(os.path.join(client.key, path))):
                client.add_message_to_all(clientIP, Message(cmd, path_len, data_len ,path))
        elif cmd == u.UPDT:
            client.send_messages_to(u.my_socket, clientIP)
            client.clear_messages(clientIP)
        elif cmd == u.FIN:
            u.communication_finished()
        else:
            print(f"invalid cmd -{cmd}-")

def accept_client(clientIP):
    cmd = u.my_socket.recv(u.COMMAND_SIZE)
    client = None
    if cmd == u.EID: # client has an ID
        client = handle_existing_client(clientIP)
    elif cmd == u.NID:
        client = handle_new_client(clientIP)
    return client
    
def start_server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("", port))
    serverSocket.listen()
    while True:
        print("waiting for client")
        u.my_socket, clientAddress = serverSocket.accept()
        clientIP = clientAddress[0]
        accept_client(clientIP)
        print(f"client {clientAddress} connected")
        handle_client(clientIP)
        print(f"client {clientAddress} dissconnected")
        u.my_socket.close()

def main():
    if len(sys.argv) < 2:
        print("Not enough args")
        return
    port = int(sys.argv[1])
    start_server(port)

if __name__ == "__main__":
    print("\nServer Active...->")
    main()