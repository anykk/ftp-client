import sys
import getpass
import socket


CR_LF = '\r\n'
MAX_LINE = 8192
FTP_PORT = 21


def create_connection(host='', port=FTP_PORT, timeout=2):
    """Creates connection if it is possible, else throw exception. Returns control socket for commands."""
    try:
        return socket.create_connection((host, port), timeout)
    except socket.gaierror as e:
        raise ConnectionError(e)


def send_cmd(sock, cmd, arg=''):
    """Sends command to server through control socket."""
    if not arg:
        sock.sendall(construct_msg(cmd, arg))
    else:
        sock.sendall(construct_msg(cmd, ' ', arg))


def get_reply(sock):
    """Gets server's reply, decode and returns it."""
    return receive_bytes(sock).decode()


def construct_msg(*args):
    """Constructs message for sending to server and converts it in bytes."""
    msg = list(args)
    msg.append(CR_LF)
    return ''.join(msg).encode()


def receive_bytes(sock):
    """Receives bytes data from server while we can."""
    answer = []
    while True:
        try:
            raw = sock.recv(MAX_LINE)
            if not raw:
                break
            answer.append(raw)
        except socket.timeout:
            break
    return b''.join(answer)


def print_reply(sock):
    """Prints server's reply."""
    reply = get_reply(sock).replace('\r\n', '')
    print(">", reply)


def user(sock):
    """USER command."""
    username = input("> USER: ")
    send_cmd(sock, "user", username)
    print_reply(sock)


def pass_(sock):
    """PASS command."""
    password = getpass.getpass("> PASS: ")
    send_cmd(sock, "pass", password)
    print_reply(sock)


if __name__ == "__main__":
    sock = create_connection('speedtest.tele2.net')
    print_reply(sock)
    send_cmd(sock, 'help')
    print_reply(sock)
    user(sock)
    pass_(sock)
    send_cmd(sock, 'help')
    """
        while True:
        cmd = input(">>>")
    """
