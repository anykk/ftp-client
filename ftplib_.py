import os
import re
import sys
import socket
import time
from exceptions import *


_pasv = True
_port = 21
_timeout = 2.75
_maxline = 8192
_crlf = '\r\n'
_re_227 = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', re.ASCII)
_re_150 = re.compile(r'150 .* \((\d+) bytes\)', re.IGNORECASE | re.ASCII)
_speed_units = ['B/s', 'KB/s', 'MB/s', 'GB/s']


def connect(host, port=_port, timeout=_timeout):
    """Connect to remote ftp. [host] & [port | default=21]"""
    try:
        return socket.create_connection((host, port), timeout)
    except socket.gaierror:
        raise AddressError(f'Wrong address: ({host}, {port}).')
    except ConnectionRefusedError:
        raise ConnectError(f'Failed to connect to ({host}, {port}).')


def _putline(control, line):
    """Send one line to the server, appending CRLF."""
    if '\r' in line or '\n' in line:
        raise IllegalLineError('an illegal newline character should not be contained')
    line = line + _crlf
    control.sendall(line.encode())


def _putcmd(control, line):  # delegate
    _putline(control, line)


def _getline(control):
    """Get one line from server, stripping CRLF."""
    line = control.recv(_maxline + 1).decode()
    if len(line) > _maxline:
        raise Error(f'got more than {_maxline} bytes')
    if not line:
        raise EOFError
    if line[-2:] == _crlf:
        line = line[:-2]
    elif line[-1:] in _crlf:
        line = line[:-1]
    return line


def _getmultiline(control):
    """Get multiline from server."""
    line = _getline(control)
    if line[3:4] == '-':
        code = line[:3]
        while 1:
            nextline = _getline(control)
            line = line + ('\n' + nextline)
            if nextline[:3] == code and \
                    nextline[3:4] != '-':
                break
    return line


def getresp(control):
    """Get response from server."""
    resp = _getmultiline(control)
    c = resp[:1]
    if c in {'1', '2', '3'}:
        return resp
    if c == '4':
        raise TempError(resp)
    if c == '5':
        raise PermError(resp)
    raise ProtoError(resp)


def voidresp(control):
    """Expect a response beginning with '2'."""
    resp = getresp(control)
    if resp[:1] != '2':
        raise ReplyError(resp)
    return resp


def sendcmd(control, cmd):
    """Send a command to server and return the response."""
    _putcmd(control, cmd)
    return getresp(control)


def voidcmd(control, cmd):
    """Send a command and expect a response beginning with '2'."""
    _putcmd(control, cmd)
    return voidresp(control)


def sendport(control, host, port):
    """Send PORT command with given host and port."""
    hbytes = host.split('.')
    pbytes = [repr(port // 256), repr(port % 256)]
    bytes = hbytes + pbytes
    cmd = 'PORT ' + ','.join(bytes)
    return voidcmd(control, cmd)


def makeport(control):
    """Create socket and send PORT command for it."""
    sock = socket.socket()
    sock.bind(('', 0))
    sock.listen(1)
    host, port = control.getsockname()[0], sock.getsockname()[1]
    resp = sendport(control, host, port)
    sock.settimeout(_timeout)
    return sock


def makepasv(control):
    """Send PASV command and get from it response host and port."""
    resp = sendcmd(control, 'PASV')
    if resp[:3] != '227':
        raise ReplyError(resp)
    m = _re_227.search(resp)
    if not m:
        raise ProtoError(resp)
    numbers = m.groups()
    host = '.'.join(numbers[:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])
    return host, port


def transfercmd(control, cmd):
    """Initiate a transfer over the data connection. It depends on preferred transfer type."""
    size_ = None
    if _pasv:
        host, port = makepasv(control)
        conn = socket.create_connection((host, port), _timeout)

        resp = sendcmd(control, cmd)
        if resp[0] == '2':
            resp = getresp(control)
        if resp[0] != '1':
            raise ReplyError(resp)
    else:
        with makeport(control) as sock:
            resp = sendcmd(control, cmd)
            if resp[0] == '2':
                resp = getresp(control)
            if resp[0] != '1':
                raise ReplyError(resp)
            conn, _ = sock.accept()
            conn.settimeout(_timeout)
    if resp[:3] == '150':
        size_ = _parse150(resp)
    return conn, size_


def makeauth(control, user='', passwd=''):
    """Authorization, default login is anonymous."""
    if not user:
        user = 'anonymous'
    if user == 'anonymous' and passwd == '':
        passwd = passwd + 'anonymous@'
    resp = sendcmd(control, 'USER ' + user)
    if resp[0] == '3':
        resp = sendcmd(control, 'PASS ' + passwd)
    if resp[0] != '2':
        raise ReplyError(resp)
    return resp


def retrbytes(control, cmd, action=None, blocksize=8192):
    """Retrieve bytes from the remote ftp."""
    conn, size = transfercmd(control, cmd)
    with conn:
        got = 0
        start_time = time.time()
        while 1:
            data = conn.recv(blocksize)
            if not data:
                break
            got += len(data)
            if size is not None:
                show_progress(got, size, start_time, time.time())
            if action:
                action(data)
    return voidresp(control)


def storbytes(control, cmd, fd, size, action=None, blocksize=8192):
    """Store bytes on the remote ftp."""
    conn = transfercmd(control, cmd)[0]
    with conn:
        got = 0
        start_time = time.time()
        while 1:
            data = fd.read(blocksize)
            if not data:
                break
            conn.sendall(data)
            got += len(data)
            if size is not None:
                show_progress(got, size, start_time, time.time())
            if action:
                action(data)
    return voidresp(control)


def sendretr(control, filename, destname=''):
    """RETR command."""
    if not destname:
        destname = filename
    with open(destname, 'wb') as fd:
        return retrbytes(control, 'RETR ' + destname, fd.write)


def sendstor(control, filename, destname=''):  # TODO: UPGRADE TO 'APPE'
    """STOR command."""
    if not destname:
        destname = filename
    size = os.path.getsize(filename)
    with open(filename, 'rb') as file:
        return storbytes(control, 'STOR ' + destname, file, size)


def sendlist(control):
    """LIST command."""
    dirs = []
    resp = retrbytes(control, 'LIST',
                     lambda x: dirs.append(x.decode()) if x[-2:] != b'\r\n' else dirs.append(x[:-2].decode()))
    return ''.join([*dirs, '\n', resp])


def sendcwd(control, dirname):
    """CWD command."""
    if dirname == '..':
        try:
            return voidcmd(control, 'CDUP')
        except PermError as msg:
            if msg.args[0][:3] != '500':
                raise
    elif dirname == '':
        dirname = '.'
    cmd = 'CWD ' + dirname
    return voidcmd(control, cmd)


def sendpwd(control):
    """PWD command."""
    resp = voidcmd(control, 'PWD')
    if resp[:3] != '257':
        raise ReplyError(resp)
    if resp[3:5] != ' "':
        return ''
    return resp


def sendsize(control, filename):
    """SIZE command."""
    resp = sendcmd(control, 'SIZE ' + filename)
    if resp[:3] == '213':
        s = resp[3:].strip()
        return int(s)


def sendquit(control):
    """QUIT command."""
    resp = voidcmd(control, 'QUIT')
    control.close()
    return resp


def show_progress(got, full, start, current):
    """Show progress: percent and download speed."""
    percent = int(round((got * 100) / full))
    try:
        speed = got / (current - start)
    except ZeroDivisionError:
        speed = 0
    i = 0
    while speed > 1024:
        speed /= 1024
        i += 1
    speed = int(round(speed))
    sys.stdout.write(f'\rGot: {percent}% Speed: {speed}{_speed_units[i]}')
    if got == full:
        sys.stdout.write('\r\n')
    sys.stdout.flush()


def _parse150(resp):
    """Parse reply, starting with 150 and get size."""
    if resp[:3] != '150':
        raise ReplyError(resp)
    m = _re_150.match(resp)
    if not m:
        return None
    return int(m.group(1))
