import os
import socket
import time

ZERO = 0x00     # empty stuff
NEWFO = 0x01    # new folder
NEWFI = 0x02    # new file
DEL = 0x03      # delete
MOV = 0x04      # move from
CHNM = 0x06     # change name of file / folder
ACK = 0x0E      # ack
FIN = 0x0F      # end of communication
MSS = 1e6

SEP = os.sep
# **************CREATING & DELETING METHODS************** #
# for tcp requests

#tested 95%
def create_folder(virtual_path, parent_folder):
    absolute_path = parent_folder + "/" + virtual_path
    # os.chmod(os.path.join(parent_folder, "dummyFolder"), mode=0o777)
    if not os.path.exists(absolute_path):
        print(f"trying to create folder named {virtual_path} on {parent_folder}")
        os.mkdir(absolute_path)
        time.sleep(0.01)

#tested 95%
def create_file(virtual_path, data_len, parent_folder, s: socket.socket):
    data: bytes
    absolute_path = parent_folder + "/" + virtual_path
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

# **************MOVING METHODS************** #


def change_name(virt_src_path, name_len, parent_folder, s: socket.socket):
    new_name = s.recv(name_len)
    abs_path = parent_folder + "/" + virt_src_path
    if os.path.exists(abs_path):
        current_name = virt_src_path.split("/")[-1]
        path = virt_src_path.split("/")[0:-1]
        os.chdir(path)
        os.rename(current_name, new_name)


def move(virt_src_path, destination_len, parent_folder, s: socket.socket):
    virt_dst_path = s.recv(destination_len)
    move_directory(virt_src_path, virt_dst_path, parent_folder)


# tested 95%
def move_file(file_name, virt_src_path, virt_dst_path, parent_folder):
    abs_src_path = parent_folder + "/" + virt_src_path + "/" + file_name
    abs_dst_path = parent_folder + "/" + virt_dst_path + "/" + file_name
    with open(abs_src_path, 'rb') as original_file:
        with open(abs_dst_path, 'wb') as new_file:
            file_data = original_file.read(int(MSS))
            while file_data != b'':
                new_file.write(file_data)
                file_data = original_file.read(int(MSS))
    delete_dir(abs_src_path)

# tested 85%
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


def communication_finished(s: socket.socket):
    print("finishing : closing socket")
    s.close()


def simulate_listen():
    print("Simulating listening")
    now = time.strftime("%d-%m-%Y %H:%M:%S")
    return bytes(now, 'utf-8')


def send(data):
    print(data)


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
def make_header(cmd: int, path_len: int, data_len: int, path: str):
    #cl_id +\
    message = cmd.to_bytes(1, 'big') +\
              path_len.to_bytes(4, 'big') +\
              data_len.to_bytes(8, 'big') +\
              bytes(path, 'utf-8')
    return message


def send_file(abs_path, virtual_path, client_id):
    # print(f"send file {abs_path}")
    header = make_header(NEWFI, len(virtual_path), os.path.getsize(abs_path), virtual_path)
    send(header)

    # notice the changes in root
    with open(abs_path, 'rb') as opened_file:
        file_data = opened_file.read(int(MSS))
        # print(f"read from file {file_data}")
        while file_data != b'':
            send(file_data)
            file_data = opened_file.read(int(MSS))


def send_folder(abs_path, virtual_path, client_id):
    header = make_header(NEWFO, len(virtual_path), 0, virtual_path)
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


def send_directory(path: bytes, client_id, main_folder):
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
