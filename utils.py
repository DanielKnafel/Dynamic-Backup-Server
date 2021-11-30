import os
import time

ZERO = 0x00     # empty stuff
NEW = 0x01
DEL = 0x02      # delete
MOVF = 0x03     # move from
MOVT = 0x04     # move to
CHNM = 0x05     # change name of file / folder
FIN = 0x0F      # end of communication
MSS = 1e6
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
def create_file(virtual_path, data_len, parent_folder):
    data: bytes
    absolute_path = parent_folder + "/" + virtual_path
    with open(absolute_path, 'wb') as new_file:
        while data_len > 0:
            data = simulate_listen()
            new_file.write(data)
            data_len -= len(data)
        time.sleep(0.05)

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


def change_name(virt_src_path, new_name):
    if os.path.exists(virt_src_path):
        pass

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
                #sub_virt_dst_path = virt_dst_path + "/" + sub_dir
                print(f"going to folder {sub_virt_src_path}")
                move_directory(sub_virt_src_path, virt_dst_path, parent_folder)
        print("deleting folder " + virt_src_path)
        delete_dir(abs_src_path)

# **************SENDING METHODS************** #


def make_header(path_len: int, file_size: int, path: str, cl_id: bytes, cmd: int):
    message = cl_id +\
              cmd.to_bytes(1, 'big') +\
              path_len.to_bytes(4, 'big') +\
              file_size.to_bytes(8, 'big') + bytes(path, 'utf-8')
    return message


def simulate_listen():
    print("Simulating listening")
    now = time.strftime("%d-%m-%Y %H:%M:%S")
    return bytes(now, 'utf-8')


def send(data):
    print(data)


def send_file(abs_path, virtual_path, client_id):
    # print(f"send file {abs_path}")
    header = make_header(len(virtual_path),
                         os.path.getsize(abs_path),
                         virtual_path,
                         client_id,
                         NEW)
    send(header)

    # notice the changes in root
    with open(abs_path, 'rb') as opened_file:
        file_data = opened_file.read(int(MSS))
        # print(f"read from file {file_data}")
        while file_data != b'':
            send(file_data)
            file_data = opened_file.read(int(MSS))


def send_folder(abs_path, virtual_path, client_id):
    header = make_header(len(virtual_path), 0, virtual_path, client_id, NEW)
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
