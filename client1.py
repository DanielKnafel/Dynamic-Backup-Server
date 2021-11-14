
from posixpath import join
import sys
import socket
import os
os.getcwd()
'''from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler'''

'''
    for root, subdirectories, files in os.walk(path):
        # CHECK FOR EMPTY FOLDER
        for file in files:
            pathCount = len(path)
            s.send(len(path))
            s.send(os.path.join(root, file))'''

'''
    s.connect((destIp, int(destPort)))
'''

'''
client1.py 123 321 ~/Desktop/Programming/IntroToNet/dummyFolder 0
'''

NEW = 0x01
EDIT = 0x02
DEL = 0x03
MOV = 0x04
MSS = 200
_destIp = _duration = 0
_destPort = _path = ''
_id = b'1234567890'
_mainFolder = ''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def makeHeader(pathLen:int, fileSize:int, path: str, id:bytes, cmd:int):
    message = id + cmd.to_bytes(1, 'big') + pathLen.to_bytes(4, 'big') + fileSize.to_bytes(8, 'big') + bytes(path, 'utf-8')
    return message

def send(data):
    print(data)

def sendDirectory(path: bytes):
    pathArr = path.split('/')
    mainFolder = pathArr[-1]
    pathArr.remove(mainFolder)
    parentPath = '/'.join(pathArr)

    for root, subdirectories, files in os.walk(path):
        shortRoot = mainFolder + "/"
        for subDir in subdirectories:
            shortPath = os.path.join(shortRoot, subDir)
            truePath = os.path.join(root, subDir)
            print(truePath)
            header = makeHeader(len(shortPath), 0, shortPath, _id, NEW)
            send(header)
            # What about files in sub directories?
    
        for file in files:
            shortPath = os.path.join(shortRoot, subDir, file)
            truePath = os.path.join(root, file)
            print(truePath)
            header = makeHeader(    len(shortPath),
                                    os.path.getsize(truePath),
                                    shortPath,
                                    _id,
                                    NEW)
            send(header)
            
            openedFile = open(truePath) # notice the changes in root 
            fileData = openedFile.read(MSS)
            while fileData != '':
                send(fileData)
                fileData = openedFile.read(MSS)

    pass

def main():    
    if len(sys.argv) >= 5:
        _destIp, _destPort, _path, _duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        if len(sys.argv) == 6:
            _id = sys.argv[5]
        sendDirectory(_path)

'''
123 321 ~/Desktop/Programming/IntroToNet/ 0
'''
if __name__ == "__main__":
    main()