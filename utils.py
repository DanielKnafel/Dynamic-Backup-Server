import os

ZERO = 0x00
NEW = 0x01
DEL = 0x02
MOVF = 0x03
MOVT = 0x04
MSS = 200

def move_folder(virt_src_path, virt_dst_path, parent_folder):
    '''#create_folder()
    abs_src_path = parent_folder + "/" + virt_src_path
    abs_dst_path = parent_folder + "/" + virt_dst_path
    # Send files

    # Send sub-folders
    for sub_dir in os.listdir(abs_path):
        if not os.path.isfile(os.path.join(abs_path, sub_dir)):
            # for sub_dir in subdirectories:
            send_folder(os.path.join(abs_path, sub_dir),
                        os.path.join(virtual_path, sub_dir),
                        client_id)'''
    pass


def move_file(virt_src_path, virt_dst_path, parent_folder):
    abs_src_path = parent_folder + "/" + virt_src_path
    abs_dst_path = parent_folder + "/" + virt_dst_path
    with open(abs_src_path, 'rb') as original_file:
        with open(abs_dst_path, 'wb') as new_file:
            file_data = original_file.read(MSS)
            while file_data != b'':
                new_file.write(file_data)
                file_data = original_file.read(MSS)
    os.remove(abs_src_path)


def move_directory(virt_src_path, virt_dst_path, parent_folder):
    if os.path.isfile(virt_src_path):
        print(f"moving file {virt_src_path} from directory")
        move_file(virt_src_path, virt_dst_path)
    else:
        print(f"moving folder {virt_src_path} from directory")
        abs_src_path = parent_folder + virt_src_path
        abs_dst_path = parent_folder + virt_dst_path
        create_folder(virt_dst_path)
        for file_name in os.listdir(abs_src_path):
            if os.path.isfile(os.path.join(abs_src_path, file_name)):
                # for file_name in files:
                move_file(virt_src_path, virt_dst_path)
        for sub_dir in os.listdir(abs_src_path):
            if not os.path.isfile(os.path.join(abs_src_path, sub_dir)):
                sub_virt_src_path = virt_src_path + "/" + sub_dir
                sub_virt_dst_path = virt_dst_path + "/" + sub_dir
                print(f"going to folder {sub_virt_src_path}")
                move_directory(sub_virt_src_path, sub_virt_dst_path)
        os.rmdir(abs_src_path)

# **************SENDING METHODS************** #


def make_header(path_len: int, file_size: int, path: str, cl_id: bytes, cmd: int):
    message = cl_id +\
              cmd.to_bytes(1, 'big') +\
              path_len.to_bytes(4, 'big') +\
              file_size.to_bytes(8, 'big') + bytes(path, 'utf-8')
    return message


def listen():
    print("Simulating listening")
    return b'.'


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
        file_data = opened_file.read(MSS)
        # print(f"read from file {file_data}")
        while file_data != b'':
            send(file_data)
            file_data = opened_file.read(MSS)


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
