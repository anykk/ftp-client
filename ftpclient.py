import sys
import getpass
import ftplib_


def setpasv(val):
    """Set PASV mode if val is True or PORT mode if val is False."""
    ftplib_._pasv = val


def open_(host, port=ftplib_._port):
    """Connect to remote ftp."""
    control = ftplib_.connect(host, port)
    print(f'Connecting to {host}...')
    resp = ftplib_.getresp(control)
    print(resp)
    return control


def user(control):
    """Send information about new user."""
    user = input('User: ')
    passwd = getpass.getpass('Password: ')
    resp = ftplib_.makeauth(control, user, passwd)
    print(resp)


def cwd(control):
    """Change working directory on the remote computer."""
    dirname = input('Directory: ')
    resp = ftplib_.sendcwd(control, dirname)
    print(resp)


def pwd(control):
    """Print working directory of the remote computer."""
    resp = ftplib_.sendpwd(control)
    print(resp)


def ls(control):
    """Print directory content of the remote computer."""
    resp = ftplib_.sendlist(control)
    print(resp)


def get(control):
    """Get file."""
    filename = input('Remote filename: ')
    if not filename:
        print('Please write filename!')
        return
    destname = input('Local filename (Default = remote filename): ')
    resp = ftplib_.sendretr(control, filename, destname)
    print(resp)


def put(control):
    """Send one file."""
    filename = input('Local filename: ')
    if not filename:
        print('Please write filename!')
        return
    destname = input('Remote filename (Default = local filename): ')
    try:
        resp = ftplib_.sendstor(control, filename, destname)
        print(resp)
    except FileNotFoundError:
        print(f"Can't find '{filename}'.", 'Please check filename.', sep='\n', file=sys.stderr)


def size(control):
    """Print size of the file of the remote computer."""
    filename = input('Remote filename: ')
    if not filename:
        print('Please write filename!')
        return
    resp = ftplib_.sendsize(control, filename)
    print(resp)


def quit_(control):
    """Close ftp session and quit."""
    resp = ftplib_.sendquit(control)
    print(resp)
    sys.exit()


def help(cmd):
    """Print short info about command."""
    if cmd == '':
        for command in COMMANDS:
            print(command)
    else:
        print(COMMANDS[cmd].__doc__)


COMMANDS = {'user': user,
            'ls': ls,
            'pwd': pwd,
            'cwd': cwd,
            'get': get,
            'put': put,
            'size': size,
            'quit': quit_,
            'help': help
            }
