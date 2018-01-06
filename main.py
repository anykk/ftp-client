import argparse


try:
    from ftp import *
except ImportError as e:
    print(e, file=sys.stderr)
    sys.exit()


def help_(cmd=None):
    """Help (commands)."""
    if cmd is None:
        print("Help about all...")
    else:
        print("Help[cmd]... Here will be dict with help...")


def parse_args():
    parser = argparse.ArgumentParser(description="Simple ftp client.")
    parser.add_argument("host", help="Host to connect.")
    parser.add_argument('port', help='Port to connect.', nargs='?', type=int, default=21)
    parser.add_argument("--passive", '-p', help="Use passive mode or not.", action="store_true", dest='passive')
    return parser.parse_args()


COMMANDS = {"ls": list_, "user": user, "pass": pass_, "cd": cwd, "pwd": pwd, "quit": quit_, "?": help_}


def main():
    args = parse_args()
    global PASV
    PASV = True if args.passive else False
    try:
        control = create_connection(args.host, args.port)
        print(f"Connecting to {args.host}...")
        print_reply(control)

        user(control)

        while True:
            input_ = input("ftp> ").split(' ')
            cmd = input_[0].lower()
            arg = input_[1] if len(input_) > 1 else ''
            try:
                COMMANDS[cmd](control, arg) if arg != '' else COMMANDS[cmd](control)
            except KeyError:
                print(f"Unsupported command {cmd}.")
            except Exception as exception:
                print(exception, file=sys.stderr)

    except ConnectionError as exception:
        print(exception, file=sys.stderr)
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
