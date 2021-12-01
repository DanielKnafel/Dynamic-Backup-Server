import socket
import sys

def send(socket, data):
    print(f"sending {data}")
    socket.send(data)

def connect_to_server(ip, port):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((ip, port))
    has_key = b'\0'
    send(clientSocket, has_key)
    key = clientSocket.recv(128)
    print(f"key is: {key.decode()}")
    path = 'test_dir'
    send(clientSocket, len(path).to_bytes(4, 'big'))
    send(clientSocket, path.encode())
    clientSocket.close()

def main():
    if len(sys.argv) < 3:
        print("Not enough args")
        return
    ip = sys.argv[1]
    port = int(sys.argv[2])
    connect_to_server(ip, port)

if __name__ == "__main__":
    print("\nTest client Active...->")
    main()