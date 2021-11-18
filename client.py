
import sys
import socket
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import LoggingEventHandler
print("delete importing time?")
'''
    s.connect((destIp, int(destPort)))
'''

# Connection
ZERO = 0x00
NEW = 0x01
DEL = 0x02
MOVF = 0x03
MOVT = 0x04
MSS = 200
# _destIp = _duration = 0
# _destPort = _path = ''
global global_id
global main_folder
global parent_folder
global moved_count
global created_flag

# **************RECEIVING METHODS************** #


def create_folder(virtual_path):
    absolute_path = parent_folder + virtual_path
    # os.chmod(os.path.join(parent_folder, "dummyFolder"), mode=0o777)
    if not os.path.exists(absolute_path):
        os.mkdir(absolute_path)


def create_file(virtual_path, data_len):
    data: bytes
    absolute_path = parent_folder + "/" + virtual_path
    with open(absolute_path, 'wb') as new_file:
        while data_len > 0:
            data = listen()
            new_file.write(data)
            data_len -= len(data)


def move_folder(virt_src_path, virt_dst_path):
    create_folder()
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


def move_file(virt_src_path, virt_dst_path):
    abs_src_path = parent_folder + "/" + virt_src_path
    abs_dst_path = parent_folder + "/" + virt_dst_path
    with open(abs_src_path, 'rb') as original_file:
        with open(abs_dst_path, 'wb') as new_file:
            file_data = original_file.read(MSS)
            while file_data != b'':
                new_file.write(file_data)
                file_data = original_file.read(MSS)
    os.remove(abs_src_path)


def move_directory(virt_src_path, virt_dst_path):
    if os.path.isfile(virt_src_path):
        move_file(virt_src_path, virt_dst_path)
    else:
        move_directory(virt_src_path, virt_dst_path)


# **************SENDING METHODS************** #


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


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


def send_directory(path: bytes, client_id):
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


def on_created(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    time.sleep(0.1)
    if os.path.isfile(directory):
        send_file(directory, virtual_path, global_id)
    else:
        send_folder(directory, virtual_path, global_id)


def on_deleted(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    dir_size = 0
    header = make_header(len(virtual_path),
                         dir_size,
                         virtual_path,
                         global_id,
                         DEL)
    send(header)


def on_modified(event):
    global moved_count
    if moved_count > 0:
        # moved_count == 2
        if moved_count > 1:
            moved_count -= 1
        # moved_count == 1
        else:

            moved_count -= 1


def on_moved(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    dir_size = 0
    header = make_header(len(directory),
                         dir_size,
                         virtual_path,
                         global_id,
                         MOVF)
    send(header)
    directory = event.dest_path
    dest_path_arr = str(directory).replace(parent_folder, '').split('/')
    virtual_path = "/".join(dest_path_arr[0:-1])
    header = make_header(len(directory),
                         dir_size,
                         virtual_path,
                         global_id,
                         MOVT)
    send(header)


# **************MAIN************** #

if __name__ == "__main__":
    print("\nClient Active...->")
    dest_ip = dir_path = my_id = ""
    dest_port = duration = 0
    if len(sys.argv) >= 5:
        dest_ip, dest_port, dir_path, duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        if len(sys.argv) == 6:
            my_id = sys.argv[5]
        else:
            my_id = b'000'
        send(make_header(len(dir_path), 0, dir_path, my_id, NEW))
        # Set globals
        global global_id
        global_id = my_id
        global main_folder
        main_folder = dir_path.split('/')[-1]
        ancestors = dir_path.split('/')[0:-1]
        global parent_folder
        parent_folder = "/".join(ancestors)
        global moved_count
        moved_count = 0
        # Communication starts
        listen()
        create_file("dummyFolder/f2/321.txt", 6)
        send_directory(dir_path, my_id)

        # Listening?
        create_folder("/dummyFolder/f2/createdByServer")
        # Watchdog
        event_handler = PatternMatchingEventHandler("[*]")
        event_handler.on_created = on_created
        event_handler.on_deleted = on_deleted
        event_handler.on_modified = on_modified
        event_handler.on_moved = on_moved

        my_observer = Observer()
        my_observer.schedule(event_handler, dir_path, recursive=True)
        my_observer.start()
        print("\n-> Watchdog Active...->")
        for x in range(1, 60):
            time.sleep(1)
        my_observer.stop()
        my_observer.join()
