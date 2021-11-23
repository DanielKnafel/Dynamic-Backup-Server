import sys
import socket
import os
import random
import string

KEY_SIZE = 128
# coded sizes in bytes
HAS_KEY_SIZE = 1
PATH_LEN_SIZE = 4
FILE_SIZE = 8

class Client:
    key = ''
    mainDirectory = ''
    # update list for all client's PCs
    devices = []

    def __init__(self, key, mainDirectory):
        self.key = key
        self.mainDirectory = mainDirectory

    def addDevice(self, clientAddress):
        if clientAddress not in self.devices:
            self.devices.append(clientAddress)
        
    def getBasePath(self):
        return os.path.join(self.key, self.mainDirectory)


clients = {}

def readHeader(clientSocket):
    pass

def recieveClientData(client, clientSocket):
    pass

def updateClient(client, clientSocket):
    pass

# New Client Handeling #
def generateKey():
    # generate a random key of length KEY_SIZE
    key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=KEY_SIZE))
    return key

def createMainClientDir(clientKey):
    print(f"creating dir {clientKey}")
    os.mkdir(clientKey)

def handleNewClient(clientSocket, clientAddress):
    key = generateKey()
    clientSocket.send(key.encode())
    createMainClientDir(key)
    pathLen = int.from_bytes(clientSocket.recv(PATH_LEN_SIZE), 'big')
    print(f"path len is: {pathLen}")
    path = clientSocket.recv(pathLen)
    print(f"path is: {path.decode()}")
    client = Client(key, path.decode())
    client.addDevice(clientAddress)
    clients[key] = client
    return client
 
# Existing Client Handeling #

def handleExistingClient(clientSocket, clientAddress):
    key = clientSocket.recv(KEY_SIZE).decode()
    client = clients[key]
    client.addDevice(clientAddress)
    return client

def handleClient(clientSocket, clientAddress):
    # check for a client key 
    hasKey = clientSocket.recv(HAS_KEY_SIZE)   
    client = None
    if hasKey != b'\0':
        print("client has key")
        client = handleExistingClient(clientSocket, clientAddress)
    else:
        print("client has no key")
        client = handleNewClient(clientSocket, clientAddress)
    recieveClientData(client, clientSocket)
    updateClient(client, clientSocket)

def startServer(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("",port))
    serverSocket.listen()
    while True:
        print("waiting for client")
        clientSocket, clientAddress = serverSocket.accept()
        print(f"client {clientAddress} connected")
        handleClient(clientSocket, clientAddress)
        print(f"client {clientAddress} dissconnected")
        clientSocket.close()

def main():
    if len(sys.argv) < 2:
        print("Not enough args")
        return
    port = int(sys.argv[1])
    startServer(port)

if __name__ == "__main__":
    print("\nServer Active...->")
    main()