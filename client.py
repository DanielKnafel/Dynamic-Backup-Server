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
global connect_info
g_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
g_socket.settimeout(0.5)
u.my_socket = g_socket


def on_created(event):
    #g_socket.connect(connect_info)
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    time.sleep(0.05)
    if os.path.exists(directory):
        if os.path.isfile(directory):
            u.send_file(directory, virtual_path, g_id)
        else:
            u.send_folder(directory, virtual_path, g_id)
    else:
        pass
        #print(f"--> Directory not exists: {directory}")
    #g_socket.close()


def on_deleted(event):
    #g_socket.connect(connect_info)
    directory = event.src_path
    virtual_path = str(directory).replace(g_parent_folder, '')
    dir_size = 0
    header = u.make_header(u.DEL, len(virtual_path), dir_size, directory, g_id)
    u.send(header)
    #g_socket.close()


def on_modified(event):
    pass


def on_moved(event):
    #g_socket.connect(connect_info)
    src_path = "".join(event.src_path)
    dst_path = "".join(event.dest_path)
    virt_src_path = str(src_path).replace(g_parent_folder, '')
    virt_dst_path = str(dst_path).replace(g_parent_folder, '')
    #print(f"---> WD src_path= {src_path}\n\tdst_path= {dst_path}")

    src_name = src_path.split("/")[-1]
    dst_name = dst_path.split("/")[-1]
    src_parent_folder = str(src_path).replace(src_name, '')
    # ignore all sub-dirs that moved
    if os.path.exists(src_parent_folder):
        if directory_moved(src_path, dst_path):
            virt_dst_path = virt_dst_path.replace("/" + dst_name, '')
            # in WD the dst contains also the name of the moved folder
            header = u.make_header(u.MOV, len(virt_src_path), len(virt_dst_path), virt_src_path, g_id)
            u.send(header)
            u.send(virt_dst_path)
        else:
            header = u.make_header(u.CHNM, len(virt_src_path), len(dst_name), virt_src_path, g_id)
            u.send(header)
            u.send(dst_name)
    else:
        # it is a sub directory, his parent already moved
        #print(f"hey {virt_src_path} your name is {dst_name}!\n\tyour father {src_parent_folder}\n\tis dead")
        pass
    time.sleep(0.05)
    #g_socket.close()


def directory_moved(full_src_path, full_dst_path):
    src_parent = full_src_path.split("/")[0:-1]
    dst_parent = full_dst_path.split("/")[0:-1]
    return src_parent != dst_parent


# **************MAIN************** #
def read_from_buffer(parent_folder, s: socket.socket, ip: str, port: int):
    s.connect(connect_info)
    cmd = u.UPDT
    header = u.make_header(cmd, 0, 0, "", g_id)
    u.send(header)
    while cmd != b'':
        cmd = s.recv(1)
        path_len = int.from_bytes(s.recv(4), 'big')
        data_len = int.from_bytes(s.recv(8), 'big')
        path = s.recv(path_len)
        if cmd == u.NEWFI:
            u.create_file(path, data_len, parent_folder, s)
        elif cmd == u.CHNM:
            u.change_name(path, data_len, parent_folder, s)
        elif cmd == u.MOV:
            u.move(path, data_len, parent_folder, s)
        elif cmd == u.NEWFO:
            u.create_folder(path, parent_folder)
        elif cmd == u.DEL:
            u.delete_dir(parent_folder + "/" + path)
        elif cmd == u.FIN:
            print(f"finished reading")
            break
        else:
            print(f"invalid cmd -{cmd}-")
            break
        time.sleep(0.005)
    try:
        s.close()
    except:
        pass


def activate(ip: str,
             port: int,
             waiting_time,
             abs_path,
             parent_folder,
             s: socket.socket):
    event_handler = PatternMatchingEventHandler("[*]")
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved

    my_observer = Observer()
    my_observer.schedule(event_handler, abs_path, recursive=True)
    my_observer.start()
    print(f"\n-> Watchdog Active(wait={waiting_time})...->")
    for x in range(1, 120):
        time.sleep(waiting_time)
        #my_observer.stop()
        #read_from_buffer(parent_folder, s, ip, port)
        #my_observer.start()
    my_observer.stop()
    my_observer.join()



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
        global connect_info
        connect_info = (dest_ip, dest_port)

        print(f"dir = {dir_path}")

        #g_socket.connect(connect_info)
        if len(sys.argv) == 6:
            g_id = sys.argv[5]
            meet_server = u.make_header(u.EID, len(dir_path), 0, dir_path, user_id=g_id)
            u.send(meet_server)
            #ack = g_socket.recv(1)
        else:
            meet_server = u.make_header(u.NID, len(dir_path), 0, dir_path)
            u.send(meet_server)
            #ack = g_socket.recv(1)
            #global_id = g_socket.recv(128)
            u.send_directory(bytes(dir_path, 'utf-8'), g_id, g_parent_folder)
        #g_socket.close()

        activate(dest_ip,
                 dest_port,
                 duration,
                 dir_path,
                 g_parent_folder,
                 g_socket)
