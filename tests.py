import unittest
from unittest import mock
import ftplib_


class Tests(unittest.TestCase):
    """Ftp functions tests."""
    def setUp(self):
        self.connection = ftplib_.socket.socket()

    def test_connect(self):
        with mock.patch('ftplib.socket.create_connection') as mocked:
            mocked.side_effect = ConnectionRefusedError()
            with self.assertRaises(ftplib_.ConnectError):
                ftplib_.connect('my_host')
        with self.assertRaises(ftplib_.AddressError):
            ftplib_.connect('my_host')

    def test_getresp(self):
        with self.connection as control:
            with mock.patch('ftplib_.socket.socket.recv',
                            side_effect=[b'1xx resp\r\n', b'4xx resp\r\n', b'5xx resp\r\n', b'strange resp\r\n']):
                self.assertEqual(ftplib_.getresp(control), '1xx resp')
                with self.assertRaises(ftplib_.TempError):
                    ftplib_.getresp(control)
                with self.assertRaises(ftplib_.PermError):
                    ftplib_.getresp(control)
                with self.assertRaises(ftplib_.ProtoError):
                    ftplib_.getresp(control)

    def test_voidresp(self):
        with self.connection as control:
            with mock.patch('ftplib_.socket.socket.recv',
                            side_effect=[b'2xx resp\r\n', b'3xx resp\r\n']):
                self.assertEqual(ftplib_.voidresp(control), '2xx resp')
                with self.assertRaises(ftplib_.ReplyError):
                    ftplib_.voidresp(control)

    def test_sendcmd(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.socket.socket.recv',
                            side_effect=[b'strange resp\r\n', b'2xx resp\r\n']):
                with self.assertRaises(ftplib_.ProtoError):
                    ftplib_.sendcmd(control, 'cmd')
                self.assertEqual(ftplib_.sendcmd(control, 'cmd'), '2xx resp')
        self.connection.close()

    def test_makeport(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.socket.socket.recv',
                            return_value=b'200 PORT command successful. Consider using PASV.\r\n'):
                port = ftplib_.makeport(control)
                self.assertTrue(type(port) == type(control))
                port.close()
        self.connection.close()

    def test_makepasv(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.socket.socket.recv',
                            return_value=b'227 Entering Passive Mode (90,130,70,73,88,36).\r\n'):
                self.assertEqual(ftplib_.makepasv(control), ('90.130.70.73', 22564))
        self.connection.close()

    def test_transfercmd(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.getresp', return_value='3xx resp'):
                with self.assertRaises(ftplib_.ReplyError):
                    ftplib_.transfercmd(control, 'cmd')
                with self.assertRaises(ftplib_.ReplyError):
                    ftplib_._pasv = False
                    ftplib_.transfercmd(control, 'cmd')
        self.connection.close()

    def test_makeauth(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.getresp', side_effect=['3xx resp', '2xx resp']):
                ftplib_.makeauth(control)
                self.assertEqual(server.recv(8192), b'USER anonymous\r\nPASS anonymous@\r\n')
        self.connection.close()

    def test_sendcwd(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.getresp',
                            side_effect=['2xx resp', '500 resp', '2xx resp']):
                self.assertEqual(ftplib_.sendcwd(control, 'dirname'), '2xx resp')
                with self.assertRaises(ftplib_.ReplyError):
                    ftplib_.sendcwd(control, '..')
                self.assertEqual(ftplib_.sendcwd(control, 'dirname'), '2xx resp')
        self.connection.close()

    def test_sendpwd(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.getresp', side_effect=['257 "/"', '2xx resp']):
                self.assertEqual(ftplib_.sendpwd(control), '257 "/"')
                with self.assertRaises(ftplib_.ReplyError):
                    ftplib_.sendpwd(control)
        self.connection.close()

    def test_sendquit(self):
        control, server = ftplib_.socket.socketpair()
        with server:
            with mock.patch('ftplib_.getresp', side_effect=['2xx bye', '500 resp']):
                self.assertEqual(ftplib_.sendquit(control), '2xx bye')
                control, server = ftplib_.socket.socketpair()
                with control, server:
                    with self.assertRaises(ftplib_.ReplyError):
                        ftplib_.sendquit(control)
        self.connection.close()

    def test_sendsize(self):
        control, server = ftplib_.socket.socketpair()
        with control, server:
            with mock.patch('ftplib_.getresp', side_effect=['213 5487', '2xx resp']):
                self.assertEqual(ftplib_.sendsize(control, 'filename'), 5487)
                self.assertEqual(ftplib_.sendsize(control, 'filename'), None)
        self.connection.close()

    def test_parse150(self):
        with self.assertRaises(ftplib_.ReplyError):
            ftplib_._parse150('342 resp')
        self.assertEqual(ftplib_._parse150('150 Opening BINARY mode data connection for 1MB.zip (1048576 bytes)'),
                         1048576)
        self.connection.close()

    def test_show_progress(self):
        with mock.patch('ftplib_.sys.stdout') as mock_stdout:
            end = ftplib_.time.time()
            ftplib_.show_progress(540, 8192, end - 4, end)
            mock_stdout.write.assert_has_calls([mock.call('\rGot: 7% Speed: 135B/s')])
        self.connection.close()


if __name__ == '__main__':
    unittest.main()
