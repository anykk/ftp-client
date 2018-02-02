import argparse


try:
    from ftpclient import *
except ImportError as _:
    print(_, file=sys.stderr)
    sys.exit()


def parse_args():
    parser = argparse.ArgumentParser(description="Simple ftp client.")
    parser.add_argument("host", help="Host to connect.")
    parser.add_argument('port', help='Port to connect.', nargs='?', type=int, default=21)
    parser.add_argument("--passive", help="Use passive mode.", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    setpasv(args.passive)
    try:
        control = open_(args.host, args.port)
        user(control)
        while 1:
            cmd = input('ftp> ').split()
            if len(cmd) >= 1 and cmd[0] == 'help':
                try:
                    help(cmd[1])
                except IndexError:
                    help('')
                except KeyError:
                    print(f"Can't show help for {cmd[1]}.")
            elif len(cmd) > 1 and cmd[0] != 'help':
                print("Commands don't take arguments.")
            else:
                try:
                    COMMANDS[cmd[0]](control)
                except KeyError:
                    print(f"{cmd[0]} cmd doesn't supports")
    except (ftplib_.ReplyError, ftplib_.TempError, ftplib_.PermError, ftplib_.ProtoError) as e:
        print(e, file=sys.stderr)
    except ftplib_.ConnectError as e:
        print(e, file=sys.stderr)
        sys.exit()
    except ftplib_.AddressError as e:
        print(e, file=sys.stderr)
        sys.exit()
    except KeyboardInterrupt:
        quit_(control)
    except ftplib_.socket.timeout:
        print('Timeout.')
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit()


if __name__ == "__main__":
    main()
