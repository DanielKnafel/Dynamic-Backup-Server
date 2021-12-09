import os
import socket
import time

# ------------------------------------------------------------------------------------- #
#                                  PROTOCOL                                             #
# Client side:                                                                          #
#   (*) First message from client to server:                                            #
#          1. client has no ID - send NID flagm recieve ID from server and send folder. #
#          2. client has an ID - send EID flag and recieve the folder.                  #
#   (*) The protocol header consists of (size in bytes):                                #
#         [CMD(1)][ID(128)][PATH_LEN(4)][DATA_LEN(8)]                                   #
#   (*) Immidietly send any changes in the client's directory to server.                #
#   (*) Establish a new connection for each message, and close it afterwards.           #
#   (*) Each connection to server includes only one update message.                     #
#   (*) Each time the client informs the server about a change, it also requests to     #
#       recieve updates from other PC's by sending the flag UPDT.                       #
# Server side:                                                                          #
#   (*) Server keeps a list of all client's PCs and saves a list of updates for each.   #
#   (*) Server sends all updates over one connection, and sends FIN afterwards.         #
# ------------------------------------------------------------------------------------- #

# coded sizes in bytes
KEY_SIZE = 128
COMMAND_SIZE = 1
PATH_LEN_SIZE = 4
FILE_SIZE = 8

# commands
NEWFO = 0x01.to_bytes(COMMAND_SIZE, 'big')  # new folder
NEWFI = 0x02.to_bytes(COMMAND_SIZE, 'big')  # new file
DEL = 0x03.to_bytes(COMMAND_SIZE, 'big')  # delete
FIN = 0x0F.to_bytes(COMMAND_SIZE, 'big')  # end of communication
NID = 0x10.to_bytes(COMMAND_SIZE, 'big')  # no id
EID = 0x11.to_bytes(COMMAND_SIZE, 'big')  # exiting id
UPDT = 0x12.to_bytes(COMMAND_SIZE, 'big')  # client to server : update ME
MSS = 1e6

my_socket: socket.socket
connect_info: socket.AddressInfo


class Message:
    cmd = 0x0
    path_len = 0
    data_len = 0
    path = ''
    data = ''

    def __init__(self, cmd, path_len, data_len, path, data=''):
        self.cmd = cmd
        self.path_len = path_len
        self.data_len = data_len
        self.path = path
        self.data = data

    def equals(self, m):
        return (self.cmd == m.cmd) and (self.path == m.path)

    def send_message(self, clientID):
        abs_path = os.path.join(clientID, self.path)
        # print(f" sending message: cmd:{self.cmd}, path: {self.path}")
        if self.cmd == NEWFI:
            send_file(my_socket, abs_path, self.path)
        elif self.cmd == NEWFO:
            send_folder(my_socket, abs_path, self.path)
        elif self.cmd == DEL:
            header = make_header(DEL, self.path_len, self.data_len, self.path)
            send(header)


# **************CREATING & DELETING METHODS************** #
# for tcp requests

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(connect_info)
    return s


def send(data):
    try:
        my_socket.send(data)
    except:
        pass


def close():
    try:
        my_socket.close()
    except:
        pass


# tested 95%
def create_folder(virtual_path, parent_folder):
    absolute_path = os.path.join(parent_folder, virtual_path)
    if not os.path.exists(absolute_path):
        # print(f"trying to create folder named {virtual_path} on {parent_folder}")
        os.mkdir(absolute_path)
        time.sleep(0.01)


# tested 95%
def create_file(s, virtual_path, data_len, parent_folder):
    data: bytes
    absolute_path = os.path.join(parent_folder, virtual_path)
    data_remain = data_len
    with open(absolute_path, 'wb') as new_file:
        while data_remain > 0:
            read_limit = min(data_remain, MSS)
            data = s.recv(read_limit)
            data_read = len(data)
            new_file.write(data)
            data_remain -= data_read
            time.sleep(0.01)


# tested 95%
def delete_dir(abs_path):
    if os.path.exists(abs_path):
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        else:
            for sub_dir in os.listdir(abs_path):
                delete_dir(os.path.join(abs_path, sub_dir))
            os.rmdir(abs_path)
    else:
        pass


# **************NOTIFY METHODS************** #
# create protocol header
def make_header(cmd: bytes,
                path_len: int,
                data_len: int,
                path: str,
                user_id=""):
    message = cmd + \
              user_id.encode() + \
              path_len.to_bytes(4, 'big') + \
              data_len.to_bytes(8, 'big') + \
              path.encode()
    return message


# use socket s to send file from a given path
def send_file(s, abs_path, virtual_path, client_id=''):
    # print(f"send v_file {virtual_path}")
    header = make_header(NEWFI, len(virtual_path), os.path.getsize(abs_path), virtual_path, client_id)
    s.send(header)

    # notice the changes in root
    with open(abs_path, 'rb') as opened_file:
        file_data = opened_file.read(int(MSS))
        # print(f"read from file {file_data}")
        while file_data != b'':
            s.send(file_data)
            file_data = opened_file.read(int(MSS))


# use socket s to send a folder, including its sub-dirs and files
def send_folder(s, abs_path, virtual_path, client_id=''):
    header = make_header(NEWFO, len(virtual_path), 0, virtual_path, client_id)
    s.send(header)
    # Send files
    for file_name in os.listdir(abs_path):
        if os.path.isfile(os.path.join(abs_path, file_name)):
            # for file_name in files:
            f_abs_path = os.path.join(abs_path, file_name)
            f_virtual_path = os.path.join(virtual_path, file_name)
            send_file(s, f_abs_path, f_virtual_path, client_id)
    # Send sub-folders
    for sub_dir in os.listdir(abs_path):
        if not os.path.isfile(os.path.join(abs_path, sub_dir)):
            # for sub_dir in subdirectories:
            send_folder(s, os.path.join(abs_path, sub_dir),
                        os.path.join(virtual_path, sub_dir),
                        client_id)


# use socket s to send a folder, including its sub-dirs and files
def send_directory(s, path, main_folder, client_id=''):
    # Request for creating main folder already done in main()
    # Send files
    for file_name in os.listdir(path):
        if os.path.isfile(os.path.join(path, file_name)):
            # for file_name in files:
            f_abs_path = os.path.join(path, file_name)
            f_virtual_path = os.path.join(main_folder, file_name)
            send_file(s, f_abs_path, f_virtual_path, client_id)
    # Send sub-folders
    for sub_dir in os.listdir(path):
        if not os.path.isfile(os.path.join(path, sub_dir)):
            # for sub_dir in subdirectories:
            sd_abs_path = os.path.join(path, sub_dir)
            sd_virtual_path = os.path.join(main_folder, sub_dir)
            send_folder(s, sd_abs_path, sd_virtual_path, client_id)