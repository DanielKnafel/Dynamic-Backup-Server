
import sys
import socket
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import utils as u
from watchdog.events import LoggingEventHandler
print("delete importing time?")


global global_id
global main_folder
global parent_folder
global ignore_folder_moved
global ignore_folder_moved_dst
global created_flag


def on_created(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    time.sleep(0.05)
    if os.path.isfile(directory):
        u.send_file(directory, virtual_path, global_id)
    else:
        u.send_folder(directory, virtual_path, global_id)


def on_deleted(event):
    directory = event.src_path
    virtual_path = str(directory).replace(parent_folder, '')
    dir_size = 0
    header = u.make_header(u.DEL,
                         len(virtual_path),
                         dir_size,
                         directory)
    send(header)


def on_modified(event):
    pass


def on_moved(event):
    global ignore_folder_moved
    global ignore_folder_moved_dst
    src_path = "".join(event.src_path)
    dst_path = b''.join(event.src_path)
    virt_src_path = str(src_path).replace(parent_folder, '')
    virt_dst_path = str(dst_path).replace(parent_folder, '')
    header = u.make_header(u.MOV, len(virt_src_path), len(virt_dst_path), virt_src_path)
    send(header)
    send(virt_dst_path)


# **************MAIN************** #
def send(data):

    print(data)


def activate(waiting_time, abs_path):
    event_handler = PatternMatchingEventHandler("[*]")
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved

    my_observer = Observer()
    my_observer.schedule(event_handler, abs_path, recursive=True)
    my_observer.start()
    print("\n-> Watchdog Active...->")

    print("\n-> TCP Active...->")
    u.send_directory(abs_path, my_id, parent_folder)

    for x in range(1, 60):
        time.sleep(waiting_time)
    my_observer.stop()
    my_observer.join()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if __name__ == "__main__":
    print("\nClient Active...->")
    dest_ip = dir_path = my_id = ""
    dest_port = duration = 0
    if len(sys.argv) < 5:
        exit()
    else:
        # BEFORE communicating with server
        dest_ip, dest_port, dir_path, duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        global global_id
        global_id = my_id
        global main_folder
        main_folder = dir_path.split('/')[-1]
        ancestors = dir_path.split('/')[0:-1]
        global parent_folder
        parent_folder = "/".join(ancestors)
        global ignore_folder_moved
        ignore_folder_moved = " "
        global ignore_folder_moved_dst
        ignore_folder_moved_dst = " "
        if len(sys.argv) == 6:
            my_id = sys.argv[5]
            send(b'1' + bytes(my_id, 'utf-8') + len(dir_path).to_bytes(4, 'big') + bytes(dir_path, 'utf-8'))
            response = u.simulate_listen()
        else:
            send(b'0' + len(dir_path).to_bytes(4, 'big') + bytes(dir_path, 'utf-8'))
            response = u.simulate_listen()
            my_id = response[1:]

        u.parse_message(b'\x01\x00\x00\x00\x13\x00\x00\x00\x00\x00\x00\x01-dummyFolder/123.txt')
