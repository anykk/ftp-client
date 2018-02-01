class Error(Exception):
    pass


class IllegalLineError(Error):
    pass


class AddressError(Error):
    pass


class ConnectError(Error):
    pass


class ReplyError(Error):  # unexpected [123]xx reply
    pass


class TempError(Error):  # 4xx errors
    pass


class PermError(Error):  # 5xx errors
    pass


class ProtoError(Error):  # response does not begin with [1-5]
    pass
