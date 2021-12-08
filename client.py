import sys
import socket
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileDeletedEvent, FileCreatedEvent, DirCreatedEvent, DirDeletedEvent
import utils as u


global g_id
global g_main_folder
global g_parent_folder
global to_do_list
to_do_list = []

# check if an event should be ignored by watchdog
def ignore_watchdog(cmd, src_path):
    m = u.Message(cmd, len(src_path), 0, src_path)
    for message in to_do_list:
        if (message.equals(m)):
            return True
    return False

def on_created(event):
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    if ignore_watchdog(u.NEWFI, virtual_path):
        return
    time.sleep(0.05)
    s = u.connect()
    if os.path.exists(directory):
        if os.path.isfile(directory):
            u.send_file(s, directory, virtual_path, g_id)
        else:
            u.send_folder(s, directory, virtual_path, g_id)
    else:
        pass
        #print(f"--> Directory not exists: {directory}")
    s.close()


def on_deleted(event):
    # print("deleted")
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    if ignore_watchdog(u.DEL, virtual_path):
        # print("ignored")
        return
    dir_size = 0
    header = u.make_header(u.DEL, len(virtual_path), dir_size, directory, g_id)
    s = u.connect()
    s.send(header)
    s.close()


def on_modified(event):
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    if ignore_watchdog(u.NEWFI, virtual_path):
        # print("ignored")
        return
    if event.is_directory:
        return None
    # print("modified")
    time.sleep(0.05)
    if os.path.exists(event.src_path):
        s = u.connect()
        u.send_file(s, directory, virtual_path, g_id)
        s.close()

def on_moved(event):
    # print("moved")   
    delete_event = None
    create_event = None

    if event.is_directory:
        delete_event = DirDeletedEvent(event.src_path)
        create_event = DirCreatedEvent(event.dest_path)
    else:
        delete_event = FileDeletedEvent(event.src_path)
        create_event = FileCreatedEvent(event.dest_path)
    on_deleted(delete_event)
    on_created(create_event)

# read the protocol header
def readHeader(s):
    path_len = int.from_bytes(s.recv(u.PATH_LEN_SIZE), 'big')
    data_len = int.from_bytes(s.recv(u.FILE_SIZE), 'big')
    path = s.recv(path_len).decode()
    return path_len, data_len, path

# **************MAIN************** #
def read_from_buffer(s, parent_folder):
    cmd = s.recv(u.COMMAND_SIZE)
    while cmd != u.FIN:
        path_len, data_len, path = readHeader(s)
        # print(f"got: \t cmd: {cmd} \n\t data_len: {data_len} \n\t path: {path}")
        to_do_list.append(u.Message(cmd, path_len, data_len, path))
        if cmd == u.NEWFI:
            u.create_file(s, path, data_len, parent_folder)
        elif cmd == u.MOV:
            u.move(path, data_len, parent_folder)
        elif cmd == u.NEWFO:
            u.create_folder(path, parent_folder)
        elif cmd == u.DEL:
            u.delete_dir(os.path.join(parent_folder, path))
        else:
            # print(f"invalid cmd -{cmd}-")
            break
        time.sleep(0.005)
        cmd = s.recv(u.COMMAND_SIZE)
    to_do_list.clear()


def activate(waiting_time, abs_path, parent_folder):
    event_handler = PatternMatchingEventHandler("[*]")
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved

    my_observer = Observer()
    my_observer.schedule(event_handler, abs_path, recursive=True)
    my_observer.start()
    # print(f"\n-> Watchdog Active(wait={waiting_time})...->")
    while True:
        time.sleep(waiting_time)
        cmd = u.UPDT
        header = u.make_header(cmd, 0, 0, "", g_id)
        s = u.connect()
        s.send(header)
        read_from_buffer(s, parent_folder)
        s.close()



if __name__ == "__main__":
    # print("\nClient Active...->")
    dest_ip = dir_path = my_id = ""
    dest_port = duration = 0
    if len(sys.argv) < 5:
        exit()
    else:
        # BEFORE communicating with server
        dest_ip, dest_port, dir_path, duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
        global g_id
        g_id = my_id
        global g_main_folder
        g_main_folder = dir_path.split('/')[-1]
        ancestors = dir_path.split('/')[0:-1]
        global g_parent_folder
        g_parent_folder = "/".join(ancestors)
        u.connect_info = (dest_ip, dest_port)

        # print(f"dir = {dir_path}")
        s = u.connect()
        if len(sys.argv) == 6:
            # print("have key")
            g_id = sys.argv[5]
            meet_server = u.make_header(u.EID, len(dir_path), 0, dir_path, user_id=g_id)
            s.send(meet_server)
            read_from_buffer(g_parent_folder)
        else:
            # print("no key")
            meet_server = u.make_header(u.NID, len(dir_path), 0, dir_path, '0' * u.KEY_SIZE)
            s.send(meet_server)
            g_id = s.recv(u.KEY_SIZE).decode()
            # print(f"got a key: {g_id}")
            u.send_directory(s, dir_path, g_main_folder, g_id)
        s.close()

        activate(duration,
                 dir_path,
                 g_parent_folder)