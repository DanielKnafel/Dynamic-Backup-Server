
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
EDIT = 0x02
DEL = 0x03
MOV = 0x04
MSS = 200
# _destIp = _duration = 0
# _destPort = _path = ''
global global_id
global main_folder
global parent_folder
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


def send_file(abs_path, virtual_path, client_id):
    header = make_header(len(virtual_path),
                         os.path.getsize(abs_path),
                         virtual_path,
                         client_id,
                         NEW)
    send(header)

    opened_file = open(abs_path)  # notice the changes in root
    file_data = opened_file.read(MSS)
    while file_data != '':
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

    if os.path.isfile(directory):
        send_file(directory, virtual_path, global_id)
    else:
        send_folder(directory, virtual_path, global_id)


def on_deleted(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    dir_size = 0
    header = make_header(len(directory),
                         dir_size,
                         virtual_path,
                         global_id,
                         DEL)
    
    send(header)



def on_modified(event):
    print(f"modified {event.src_path}")


def on_moved(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    dir_size = 0
    header = make_header(len(directory),
                         dir_size,
                         virtual_path,
                         global_id,
                         MOV)
    send(header)


'''
123 321 ~/Desktop/Programming/IntroToNet/ 0
'''

if __name__ == "__main__":
    print("\nClient Active...->")
    dest_ip = dir_path = my_id = ""
    dest_port = duration = 0
    if len(sys.argv) >= 5:
        dest_ip, dest_port, dir_path, duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        if len(sys.argv) == 6:
            my_id = sys.argv[5]
            send(make_header(0, 0, '', my_id, NEW))
        else:
            my_id = b'000'
            send(make_header(0, 0, dir_path, my_id, NEW))
        # Set globals
        global_id = my_id
        print(f"dp = {dir_path}")
        main_folder = dir_path.split('/')[-1]
        ancestors = dir_path.split('/')[0:-1]
        print(f"anc = {ancestors}")
        parent_folder = "/".join(ancestors)
        print(f"pf = {parent_folder}")
        # Communication starts
        listen()
        send_directory(dir_path, my_id)

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
    for x in range(1, 30):
        time.sleep(1)
    my_observer.stop()
    my_observer.join()
