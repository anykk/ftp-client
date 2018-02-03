# ftp-client
Simple python3 ftp-client implementation based on sockets.
## How to run:
> python main.py [-h] [--passive] host [port]
> by default port is 21 and passive is false (active mode has used)
> ,commands:
- user - authorize with login and password
- cd - change current directory
- pwd - show name of current directory
- ls - show listing of current directory
- get - get remote file into current directory
- put - put local file into remote ftp
- size - show size of chosen file
- quit - quit from ftp client
> for help use "help" command
