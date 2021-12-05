import os
import socket
import time

# coded sizes in bytes
KEY_SIZE = 128
COMMAND_SIZE = 1
PATH_LEN_SIZE = 4
FILE_SIZE = 8

# commands
ZERO = 0x00.to_bytes(COMMAND_SIZE, 'big')     # empty stuff
NEWFO = 0x01.to_bytes(COMMAND_SIZE, 'big')    # new folder
NEWFI = 0x02.to_bytes(COMMAND_SIZE, 'big')    # new file
DEL = 0x03.to_bytes(COMMAND_SIZE, 'big')      # delete
MOV = 0x04.to_bytes(COMMAND_SIZE, 'big')      # move from
CHNM = 0x06.to_bytes(COMMAND_SIZE, 'big')     # change name of file / folder
ACK = 0x0E.to_bytes(COMMAND_SIZE, 'big')      # ack
FIN = 0x0F.to_bytes(COMMAND_SIZE, 'big')      # end of communication
NID = 0x10.to_bytes(COMMAND_SIZE, 'big')      # no id
EID = 0x11.to_bytes(COMMAND_SIZE, 'big')      # exiting id
UPDT = 0x12.to_bytes(COMMAND_SIZE, 'big')     # client to server : update ME
MSS = 1e6

SEP = os.sep
my_socket: socket.socket
connect_info : socket.AddressInfo

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
    
    def equals(self, m):
        return (self.cmd == m.cmd) and (self.path == m.path)


    def send_message(self, clientID):
        abs_path = os.path.join(clientID, self.path)
        if self.cmd == NEWFI:
            send_file(abs_path, self.path)
        elif self.cmd == CHNM:
            pass
        elif self.cmd == MOV:
            header = make_header(MOV, self.path_len, self.data_len, self.path, '')
            send(header)
            send(self.data)
        elif self.cmd == NEWFO:
            send_folder(abs_path, self.path)
        elif self.cmd == DEL:
            header = make_header(DEL, self.path_len, self.data_len, self.path)
            send(header)


# **************CREATING & DELETING METHODS************** #
# for tcp requests

def connect():
    global my_socket
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # my_socket.settimeout(0.1)
    my_socket.connect(connect_info)

#tested 95%
def create_folder(virtual_path, parent_folder):
    absolute_path = parent_folder + "/" + virtual_path
    # os.chmod(os.path.join(parent_folder, "dummyFolder"), mode=0o777)
    if not os.path.exists(absolute_path):
        print(f"trying to create folder named {virtual_path} on {parent_folder}")
        os.mkdir(absolute_path)
        time.sleep(0.01)


#tested 95%
def create_file(virtual_path, data_len, parent_folder):
    data: bytes
    absolute_path = parent_folder + "/" + virtual_path
    data_remain = data_len
    with open(absolute_path, 'wb') as new_file:
        while data_remain > 0:
            read_limit = min(data_remain, MSS)
            data = my_socket.recv(read_limit)
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

# **************MOVING METHODS************** #

def change_name(virt_src_path, name_len, parent_folder):
    new_name = my_socket.recv(name_len).decode()
    abs_path = os.path.join(parent_folder, virt_src_path)
    if os.path.exists(abs_path):
        # get parent folders
        path = abs_path.split("/")[0:-1]
        path = "/".join(path)
        new_name = os.path.join(path, new_name)
        os.rename(abs_path, new_name)
    else:
        pass

def move(virt_src_path, destination_len, parent_folder):
    virt_dst_path = my_socket.recv(destination_len).decode()
    if os.path.exists(parent_folder + "/" + virt_src_path):
        move_directory(virt_src_path, virt_dst_path, parent_folder)
    else:
        pass
    return virt_dst_path


# existence verification in move()
def move_file(file_name, virt_src_path, virt_dst_path, parent_folder):
    abs_src_path = parent_folder + "/" + virt_src_path + "/" + file_name
    abs_dst_path = parent_folder + "/" + virt_dst_path + "/" + file_name
    if os.path.exists(abs_src_path):
        with open(abs_src_path, 'rb') as original_file:
            with open(abs_dst_path, 'wb') as new_file:
                file_data = original_file.read(int(MSS))
                while file_data != b'':
                    new_file.write(file_data)
                    file_data = original_file.read(int(MSS))
        delete_dir(abs_src_path)
    else:
        pass


# existence verification in move()
def move_directory(virt_src_path, virt_dst_path, parent_folder):
    if os.path.isfile(parent_folder + "/" + virt_src_path):
        file_name = virt_src_path.split("/")[-1]
        print(f"moving file {file_name} from directory " + virt_src_path)
        move_file(file_name, virt_src_path, virt_dst_path, parent_folder)
    else:
        folder_name = virt_src_path.split("/")[-1]
        print(f"moving folder {folder_name} from directory " + virt_src_path)
        abs_src_path = parent_folder + "/" + virt_src_path
        # abs_dst_path = parent_folder + "/" + virt_dst_path
        virt_dst_path = virt_dst_path + "/" + folder_name
        create_folder(virt_dst_path, parent_folder)
        for file_name in os.listdir(abs_src_path):
            if os.path.isfile(os.path.join(abs_src_path, file_name)):
                print("moving file " + file_name + " from " + virt_src_path)
                # for file_name in files:
                move_file(file_name, virt_src_path, virt_dst_path, parent_folder)
        for sub_dir in os.listdir(abs_src_path):
            if not os.path.isfile(os.path.join(abs_src_path, sub_dir)):
                sub_virt_src_path = virt_src_path + "/" + sub_dir
                print(f"going to folder {sub_virt_src_path}")
                move_directory(sub_virt_src_path, virt_dst_path, parent_folder)
        print("deleting folder " + virt_src_path)
        delete_dir(abs_src_path)


# **************COMMUNICATION METHODS************** #


def communication_finished():
    print("finishing : closing socket")
    my_socket.close()


def simulate_listen():
    print("Simulating listening")
    now = time.strftime("%d-%m-%Y %H:%M:%S")
    return bytes(now, 'utf-8')


def send(data):
    print(f"sending: {data}")
    try:
        my_socket.send(data)
    except:
        pass
        #print(f"socket error. can't send {data}")
    # USE GLOBAL s


# NOT for 1st message
# For now - probably good only for client
'''def read_from_buffer(parent_folder, s: socket.socket, ip: bytes, port: int):
    s.connect((ip, port))
    cmd = b'start'
    while cmd != b'':
        cmd = s.recv(1)
        path_len = int.from_bytes(s.recv(4), 'big')
        data_len = int.from_bytes(s.recv(8), 'big')
        path = s.recv(path_len)
        if cmd == NEWFI:
            create_file(path, data_len, parent_folder, s)
        elif cmd == CHNM:
            change_name(path, data_len, parent_folder, s)
        elif cmd == MOV:
            move(path, data_len, parent_folder, s)
        elif cmd == NEWFO:
            create_folder(path, parent_folder)
        elif cmd == DEL:
            delete_dir(parent_folder + "/" + path)
        elif cmd == FIN:
            communication_finished(s)
        else:
            print(f"invalid cmd -{cmd}-")
        time.sleep(0.005)
    try:
        s.close()
    except:
        pass'''


# **************NOTIFY METHODS************** #
def make_header(cmd: bytes,
                path_len: int,
                data_len: int,
                path: str,
                user_id=""):
    message = cmd + \
              user_id.encode() + \
              path_len.to_bytes(4, 'big') +\
              data_len.to_bytes(8, 'big') +\
              path.encode()
    return message


def send_file(abs_path, virtual_path, client_id=''):
    # print(f"send v_file {virtual_path}")
    header = make_header(NEWFI, len(virtual_path), os.path.getsize(abs_path), virtual_path, client_id)
    send(header)

    # notice the changes in root
    with open(abs_path, 'rb') as opened_file:
        file_data = opened_file.read(int(MSS))
        # print(f"read from file {file_data}")
        while file_data != b'':
            send(file_data)
            file_data = opened_file.read(int(MSS))

def send_folder(abs_path, virtual_path, client_id=''):
    header = make_header(NEWFO, len(virtual_path), 0, virtual_path, client_id)
    send(header)
    # Send files
    for file_name in os.listdir(abs_path):
        if os.path.isfile(os.path.join(abs_path, file_name)):
            # for file_name in files:
            f_abs_path = os.path.join(abs_path, file_name)
            f_virtual_path = os.path.join(virtual_path, file_name)
            send_file(f_abs_path, f_virtual_path, client_id)
    # Send sub-folders
    for sub_dir in os.listdir(abs_path):
        if not os.path.isfile(os.path.join(abs_path, sub_dir)):
            # for sub_dir in subdirectories:
            send_folder(os.path.join(abs_path, sub_dir),
                        os.path.join(virtual_path, sub_dir),
                        client_id)


def send_directory(path, main_folder, client_id=''):
    # Request for creating main folder already done in main()
    # Send files
    for file_name in os.listdir(path):
        if os.path.isfile(os.path.join(path, file_name)):
            # for file_name in files:
            f_abs_path = os.path.join(path, file_name)
            f_virtual_path = os.path.join(main_folder, file_name)
            send_file(f_abs_path, f_virtual_path, client_id)
    # Send sub-folders
    for sub_dir in os.listdir(path):
        if not os.path.isfile(os.path.join(path, sub_dir)):
            # for sub_dir in subdirectories:
            sd_abs_path = os.path.join(path, sub_dir)
            sd_virtual_path = os.path.join(main_folder, sub_dir)
            send_folder(sd_abs_path, sd_virtual_path, client_id)