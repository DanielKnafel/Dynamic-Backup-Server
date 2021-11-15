
import sys
import socket
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

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

ZERO = 0x00
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


def make_header(path_len: int, file_size: int, path: str, cl_id: bytes, cmd: int):
    message = cl_id +\
              cmd.to_bytes(1, 'big') +\
              path_len.to_bytes(4, 'big') +\
              file_size.to_bytes(8, 'big') + bytes(path, 'utf-8')
    return message


def listen():
    print("Simulating listening")


def send(data):
    print(data)


def send_file(file, abs_path, virtual_path):
    header = make_header(len(virtual_path),
                         os.path.getsize(abs_path),
                         virtual_path,
                         _id,
                         NEW)
    send(header)

    opened_file = open(abs_path)  # notice the changes in root
    file_data = opened_file.read(MSS)
    while file_data != '':
        send(file_data)
        file_data = opened_file.read(MSS)


def send_folder(abs_path, virtual_path):
    header = make_header(len(virtual_path), 0, virtual_path, _id, NEW)
    send(header)
    for root, subdirectories, files in os.walk(abs_path):
        for file_name in files:
            f_abs_path = os.path.join(abs_path, file_name)
            f_virtual_path = os.path.join(virtual_path, file_name)
            send_file(file_name, f_abs_path, f_virtual_path)
        for sub_dir in subdirectories:
            send_folder(os.path.join(root, sub_dir),
                        os.path.join(virtual_path, sub_dir))
    pass


def send_directory(path: bytes):
    path_arr = path.split('/')
    main_folder = path_arr[-1]
    path_arr.remove(main_folder)
    # Request for creating main folder already done in main()
    for root, subdirectories, files in os.walk(path):
        for file_name in files:
            f_abs_path = os.path.join(path, file_name)
            f_virtual_path = os.path.join(main_folder, file_name)
            send_file(file_name, f_abs_path, f_virtual_path)
        for sub_dir in subdirectories:
            sd_abs_path = os.path.join(path, sub_dir)
            sd_virtual_path = os.path.join(main_folder, sub_dir)
            send_folder(sd_abs_path, sd_virtual_path)


def main():
    global _id
    if len(sys.argv) >= 5:
        _destIp, _destPort, _path, _duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        if len(sys.argv) == 6:
            _id = sys.argv[5]
            send(make_header(0, 0, '', _id, NEW))
        else:
            send(make_header(0, 0, _path, _id, NEW))
        listen()
        send_directory(_path)


'''
123 321 ~/Desktop/Programming/IntroToNet/ 0
'''
if __name__ == "__main__":
    print("\nClient Active...->")
    main()