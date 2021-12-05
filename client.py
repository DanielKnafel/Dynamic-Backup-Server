import sys
import socket
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import utils as u


global g_id
global g_main_folder
global g_parent_folder
global to_do_list
to_do_list = []

def ignore_watchdog(cmd, src_path):
    m = u.Message(cmd, len(src_path), 0, src_path)
    for message in to_do_list:
        if (message.eqauls(m)):
            return True
    return False

def on_created(event):
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    if ignore_watchdog(u.NEWFI, virtual_path) or ignore_watchdog(u.NEWFO, virtual_path):
        return
    time.sleep(0.05)
    u.connect()
    if os.path.exists(directory):
        if os.path.isfile(directory):
            u.send_file(directory, virtual_path, g_id)
        else:
            u.send_folder(directory, virtual_path, g_id)
    else:
        pass
        #print(f"--> Directory not exists: {directory}")
    u.communication_finished()


def on_deleted(event):
    print("deleted")
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    if ignore_watchdog(u.DEL, virtual_path):
        print("ignored")
        return
    dir_size = 0
    header = u.make_header(u.DEL, len(virtual_path), dir_size, directory, g_id)
    u.connect()
    u.send(header)
    u.communication_finished()


def on_modified(event):
    # if ignore_watchdog(u.NEWFI, virtual_path) or ignore_watchdog(u.NEWFO, virtual_path):
        
    print("modified")


def on_moved(event):
    print("moved")
    src_path = "".join(event.src_path)
    dst_path = "".join(event.dest_path)
    virt_src_path = str(src_path).replace(g_parent_folder, '')
    virt_dst_path = str(dst_path).replace(g_parent_folder, '')
    #print(f"---> WD src_path= {src_path}\n\tdst_path= {dst_path}")
    if ignore_watchdog(u.MOV, virt_src_path) or ignore_watchdog(u.CHNM, virt_src_path):
        return
    src_name = src_path.split("/")[-1]
    dst_name = dst_path.split("/")[-1]
    src_parent_folder = str(src_path).replace(src_name, '')
    u.connect()
    # ignore all sub-dirs that moved
    if os.path.exists(src_parent_folder):
        if directory_moved(src_path, dst_path):
            virt_dst_path = virt_dst_path.replace("/" + dst_name, '')
            # in WD the dst contains also the name of the moved folder
            header = u.make_header(u.MOV, len(virt_src_path), len(virt_dst_path), virt_src_path, g_id)
            u.send(header)
            u.send(virt_dst_path.encode())
        else:
            header = u.make_header(u.CHNM, len(virt_src_path), len(dst_name), virt_src_path, g_id)
            u.send(header)
            u.send(dst_name.encode())
    else:
        # it is a sub directory, his parent already moved
        #print(f"hey {virt_src_path} your name is {dst_name}!\n\tyour father {src_parent_folder}\n\tis dead")
        pass
    time.sleep(0.05)
    u.communication_finished()


def directory_moved(full_src_path, full_dst_path):
    src_parent = full_src_path.split("/")[0:-1]
    dst_parent = full_dst_path.split("/")[0:-1]
    return src_parent != dst_parent


# **************MAIN************** #
def read_from_buffer(parent_folder):
    cmd = u.UPDT
    header = u.make_header(cmd, 0, 0, "", g_id)
    u.connect()
    u.send(header)
    cmd = u.my_socket.recv(u.COMMAND_SIZE)
    while cmd != u.FIN:
        print(f"cmd is: -{cmd}-")
        path_len = int.from_bytes(u.my_socket.recv(u.PATH_LEN_SIZE), 'big')
        data_len = int.from_bytes(u.my_socket.recv(u.FILE_SIZE), 'big')
        path = u.my_socket.recv(path_len)
        if cmd == u.NEWFI:
            u.create_file(path, data_len, parent_folder)
        elif cmd == u.CHNM:
            u.change_name(path, data_len, parent_folder)
        elif cmd == u.MOV:
            u.move(path, data_len, parent_folder)
        elif cmd == u.NEWFO:
            u.create_folder(path, parent_folder)
        elif cmd == u.DEL:
            u.delete_dir(parent_folder + "/" + path)
        else:
            print(f"invalid cmd -{cmd}-")
            break
        to_do_list.append(u.Message(cmd, path_len, data_len, path))
        time.sleep(0.005)
        cmd = u.my_socket.recv(u.COMMAND_SIZE)
    u.communication_finished()


def activate(waiting_time, abs_path, parent_folder):
    event_handler = PatternMatchingEventHandler("[*]")
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved

    my_observer = Observer()
    my_observer.schedule(event_handler, abs_path, recursive=True)
    my_observer.start()
    print(f"\n-> Watchdog Active(wait={waiting_time})...->")
    while True:
        pass
    #     time.sleep(waiting_time)
    #     read_from_buffer(parent_folder)


if __name__ == "__main__":
    print("\nClient Active...->")
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

        print(f"dir = {dir_path}")
        u.connect()
        if len(sys.argv) == 6:
            print("have key")
            g_id = sys.argv[5]
            meet_server = u.make_header(u.EID, len(dir_path), 0, dir_path, user_id=g_id)
            u.send(meet_server)
            #ack = g_socket.recv(1)
        else:
            print("no key")
            meet_server = u.make_header(u.NID, len(dir_path), 0, dir_path, '0' * u.KEY_SIZE)
            u.send(meet_server)
            #ack = g_socket.recv(1)
            g_id = u.my_socket.recv(u.KEY_SIZE).decode()
            print(f"got a key: {g_id}")
            u.send_directory(dir_path, g_main_folder, g_id)
        u.communication_finished()

        activate(duration,
                 dir_path,
                 g_parent_folder)