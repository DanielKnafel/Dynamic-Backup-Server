import sys
import socket
import os
import random
import string

# coded sizes in bytes
KEY_SIZE = 128
PATH_LEN = 4
FILE_SIZE = 8

def generateKey():
    # generate a random, KEY_SIZE-long, key
    key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=KEY_SIZE))
    return key

def handleExistingClient(clientSocket):
    key = clientSocket.recv(KEY_SIZE)

def createMainClientDir(dirName):
    os.mkdir(dirName)

# def backupDir(path):


def handleNewClient(clientSocket):
    key = generateKey()
    clientSocket.send(key)
    createMainClientDir(key)
    pathLen = clientSocket.recv(PATH_LEN)
    path = clientSocket.recv(pathLen)
    # backupDir(path)

def handleClient(clientSocket):
    # check for a client key 
    hasKey = clientSocket.recv(1)
    if hasKey:
        handleExistingClient(clientSocket)
    else:
        handleNewClient(clientSocket)

def startServer(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(port)
    serverSocket.listen()
    while True:
        clientSocket, clientAddress = serverSocket.accept()
        handleClient(clientSocket)

def main():
    if len(sys.argv) < 2:
        return
    port = int(sys.argv[1])
    startServer(port)
    

        


'''
123 321 ~/Desktop/Programming/IntroToNet/ 0
'''
if __name__ == "__main__":
    print("\nServer Active...->")
    main()