import sys
import argparse


try:
    import ftplib_
except ImportError as _:
    print(_, file=sys.stderr)
    sys.exit()


def help_():
    """Help (commands)."""
    print('help')


def parse_args():
    parser = argparse.ArgumentParser(description="Simple ftp client.")
    parser.add_argument("host", help="Host to connect.")
    parser.add_argument('port', help='Port to connect.', nargs='?', type=int, default=21)
    parser.add_argument("--passive", help="Use passive mode.", action="store_true")
    return parser.parse_args()


def main():
    pass


if __name__ == "__main__":
    main()
