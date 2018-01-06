import sys
import socket
import re
import getpass
from random import randint


PASV = False
ADDR_PATTERN = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)')
CR_LF = '\r\n'
MAX_LINE = 8192
MAX_WIN = 65535
FTP_PORT = 21


def create_connection(host='', port=FTP_PORT, timeout=2):
    """Creates connection if it is possible, else throw exception. Returns control socket for commands."""
    try:
        return socket.create_connection((host, port), timeout)
    except socket.gaierror as e:
        raise ConnectionError(e)


def send_cmd(control, cmd, arg=''):
    """Sends command to server through control socket."""
    if not arg:
        control.sendall(construct_msg(cmd, arg))
    else:
        control.sendall(construct_msg(cmd, ' ', arg))


def get_reply(control):
    """Gets server's reply, decode and returns it."""
    return receive_bytes(control, MAX_LINE).decode()


def construct_msg(*args):
    """Constructs message for sending to server and converts it in bytes."""
    msg = list(args)
    msg.append(CR_LF)
    return ''.join(msg).encode()


def receive_bytes(connection, buf_size):
    """Receives bytes data from server while we can."""
    answer = []
    while True:
        try:
            raw = connection.recv(buf_size)
            if not raw:
                break
            answer.append(raw)
        except socket.timeout:
            break
    return b''.join(answer)


def print_reply(control):
    """Prints server's reply."""
    reply = get_reply(control).replace('\r\n', '')
    print(reply)


def user(control):
    """USER command."""
    username = input("USER: ")
    send_cmd(control, "user", username)
    reply = get_reply(control).replace('\r\n', '')
    print(reply)
    if reply[0] == '5':
        print("Login error.")
    else:
        pass_(control)


def pass_(control):
    """PASS command."""
    password = getpass.getpass("PASS: ")
    send_cmd(control, "pass", password)
    print_reply(control)


def pasv(control):  # <--- PASSIVE MODE
    """PASV command. Initiate data connection.."""
    send_cmd(control, "pasv")
    reply = get_reply(control)
    print(reply.replace('\r\n', ''))
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
    send_cmd(control, "port", address)
    print_reply(control)
    return conn_handler


def get_data(control, cmd):
    """Gets data by command depends on active/passive mode."""
    if not PASV:
        temp = port_(control)
        send_cmd(control, cmd)
        print(control.recv(MAX_LINE).decode().replace('\r\n', ''))  # msg before data transport
        data_conn, addr = temp.accept()
    else:
        data_conn = pasv(control)
        send_cmd(control, cmd)
        print(control.recv(MAX_LINE).decode().replace('\r\n', ''))  # msg before data transport
    return receive_bytes(data_conn, MAX_WIN).decode()


def list_(control):
    """LIST command."""
    data = get_data(control, "list")
    print(data[:-1])  # remove last \r\n
    print_reply(control)


def cwd(control, path):
    """CWD command."""
    if path == "..":
        send_cmd(control, "cdup")
    else:
        send_cmd(control, "cwd", path)
    print_reply(control)


def pwd(control):
    """PWD command."""
    send_cmd(control, "pwd")
    print_reply(control)


def quit_(control):
    """QUIT command."""
    send_cmd(control, "quit")
    print_reply(control)
    sys.exit()

