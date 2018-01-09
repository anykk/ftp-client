import sys
import argparse


try:
    import ftp
except ImportError as e:
    print(e, file=sys.stderr)
    sys.exit()


def help_():
    """Help (commands)."""
    print("ls - list dir\r\nuser - user for login\r\nget - download file in current dir"
          "cd - change directory\r\npwd - current directory\r\nquit - quit from app\r\n"
          "...")


def parse_args():
    parser = argparse.ArgumentParser(description="Simple ftp client.")
    parser.add_argument("host", help="Host to connect.")
    parser.add_argument('port', help='Port to connect.', nargs='?', type=int, default=21)
    parser.add_argument("--passive", help="Use passive mode.", action="store_true")
    return parser.parse_args()


COMMANDS = {"ls": ftp.list_, "user": ftp.user, "cd": ftp.cwd, "pwd": ftp.pwd, "get": ftp.get, "quit": ftp.quit_, "help": help_}


def main():
    args = parse_args()
    ftp.PASV = True if args.passive else False
    try:
        control = ftp.connect(args.host, args.port)
        print(f"Connecting to {args.host}...")
        ftp.print_reply(control)

        ftp.user(control)

        while True:
            input_ = input("ftp> ").split(' ')
            cmd = input_[0].lower()
            arg = input_[1] if len(input_) > 1 else ''
            try:
                if cmd == 'help' or cmd == '?':
                    help_()
                else:
                    COMMANDS[cmd](control, arg) if arg != '' else COMMANDS[cmd](control)
            except KeyError:
                print(f"Unsupported command {cmd}.", file=sys.stderr)
            except TypeError:
                print(f"Command {cmd} doesn't takes arguments.", file=sys.stderr)
            except Exception as exception:
                print(exception, file=sys.stderr)
                sys.exit()

    except ConnectionError as exception:
        print(exception, file=sys.stderr)
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
