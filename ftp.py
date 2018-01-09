import sys
import socket
import re
import getpass
import time
from random import randint


PASV = False
ADDR_PATTERN = re.compile(r'\d+,\d+,\d+,\d+,\d+,\d+')
SIZE_PATTERN = re.compile(r'\((\d+) bytes\)')
CR_LF = '\r\n'
MAX_LINE = 8192
MAX_WIN = 65535
FTP_PORT = 21
SPEED_UNITS = ['B/s', 'KB/s', 'MB/s', 'GB/s']


def connect(host='', port=FTP_PORT, timeout=2):
    """Connect to remote server. [host] & [port, default=21]"""
    try:
        return socket.create_connection((host, port), timeout)
    except socket.gaierror:
        print(f"Wrong address: ({host}, {port}).")
        sys.exit()


def quote(control, cmd, arg=''):
    """Sends command to server through control socket."""
    if not arg:
        control.sendall(construct_msg(cmd, arg))
    else:
        control.sendall(construct_msg(cmd, ' ', arg))


def recv_reply(control):
    """Gets server's reply. (for simple commands)"""
    return receive_bytes(control).decode()


def construct_msg(*args):
    """Constructs message from args for sending to server."""
    msg = list(args)
    msg.append(CR_LF)
    return ''.join(msg).encode()


def receive_bytes(connection):
    """Receives bytes from server while we can."""
    data = []
    while True:
        try:
            raw = connection.recv(MAX_LINE)
            if not raw:
                break
            data.append(raw)
        except socket.timeout:
            break
    return b''.join(data)


def print_reply(control):
    """Prints server's reply."""
    reply = recv_reply(control)[:-1]
    print(reply)


def user(control):
    """Login with user and password."""
    username = input("User: ")
    quote(control, "user", username)
    reply = recv_reply(control).replace('\r\n', '')
    print(reply)
    if reply[0] == '5':
        print("Login error.")
    else:
        pass_(control)


def pass_(control):
    """PASS command."""
    password = getpass.getpass("Password: ")
    quote(control, "pass", password)
    print_reply(control)


def pasv(control):  # <--- PASSIVE MODE
    """PASV command. Initiate data connection."""
    quote(control, "pasv")
    reply = recv_reply(control)
    print(reply[:-1])
    address = re.findall(ADDR_PATTERN, reply)[0]
    host, port = '.'.join(address[:4]), int(address[4])*256 + int(address[5])
    data_conn = socket.create_connection((host, port))
    return data_conn


def port_(control):  # <--- ACTIVE MODE
    """PORT command. Server initiates connection."""
    conn_handler = socket.socket()
    conn_handler.bind((control.getsockname()[0], randint(1024, 65535)))
    conn_handler.listen(1)
    host, port = conn_handler.getsockname()
    address = f"{host.replace('.', ',')},{port // 256},{port % 256}"
    quote(control, "port", address)
    print_reply(control)
    return conn_handler


def recv_through_data_conn(control, cmd, arg=''):
    """Gets data by command depends on active/passive mode."""
    if not PASV:
        conn_handler = port_(control)
        quote(control, cmd, arg)
        reply = control.recv(MAX_LINE).decode()[:-1]  # msg before data transfer
        print(reply)
        data_conn, _ = conn_handler.accept()
    else:
        data_conn = pasv(control)
        quote(control, cmd, arg)
        reply = control.recv(MAX_LINE).decode()[:-1]
        print(reply)  # msg before data transfer
    data = receive_bytes(data_conn).decode()
    data_conn.close()
    return data


def list_(control):
    """Listing of current directory."""
    data = recv_through_data_conn(control, "list")
    print(data[:-1])
    print_reply(control)


def cwd(control, path):
    """Change working directory."""
    if path == "..":
        quote(control, "cdup")
    else:
        quote(control, "cwd", path)
    print_reply(control)


def pwd(control):
    """Current working directory."""
    quote(control, "pwd")
    print_reply(control)


def progress(received, full, start, current):
    """Flushes downloading progress. (percents and speed)"""
    percent = int(round((received * 100) / full))
    speed = received / (current - start)
    i = 0
    while speed > 1024:
        speed /= 1024
        i += 1
    speed = int(round(speed))
    sys.stdout.write(f"\rDownloaded: {percent}% Speed: {speed}{SPEED_UNITS[i]}")
    sys.stdout.flush()


def get(control, filename):
    """Download remote file in current directory."""
    if PASV:
        data_conn = pasv(control)
        quote(control, "retr", filename)
        reply = recv_reply(control)
    else:
        conn_handler = port_(control)
        quote(control, "retr", filename)
        reply = recv_reply(control)
        data_conn, _ = conn_handler.accept()
    print(reply[:-1])
    size = int(re.findall(SIZE_PATTERN, reply)[0])
    with open(filename, "wb") as file:
        received = 0
        start = time.time()
        while True:
            raw = data_conn.recv(MAX_WIN)
            if not raw:
                break
            received += len(raw)
            file.write(raw)
            progress(received, size, start, time.time())
    sys.stdout.write("\r\n")
    sys.stdout.flush()
    data_conn.close()
    print_reply(control)
# TODO : put, append


def quit_(control):
    """Ends session and quit from server."""
    quote(control, "quit")
    print_reply(control)
    sys.exit()

