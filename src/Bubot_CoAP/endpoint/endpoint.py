import logging
import socket
import asyncio

logger = logging.getLogger(__name__)


class Endpoint:
    _scheme = None

    def __init__(self, **kwargs):
        self.params = kwargs
        self._multicast = None
        self._address = None
        self._family = None
        self.lock = asyncio.Lock()

    @property
    def multicast(self):
        return self._multicast

    @property
    def scheme(self):
        return self._scheme

    @property
    def address(self):
        return self._address[0], self._address[1]

    # @address.setter
    # def address(self, value):
    #     self._address = value

    @property
    def family(self):
        return self._family

    async def listen(self, server):
        raise NotImplementedError()

    def send(self, data, address):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __del__(self):
        self.close()

    async def restart_transport(self, server):
        raise NotImplementedError()


    def calc_family_by_address(self, address):
        if address[0] == '' or address[0] is None:
            self._family = socket.AF_INET
            self._address = ('', address[1])
        elif address[0] == '::':
            self._family = socket.AF_INET6
            self._address = ('[::]', address[1])
        else:
            self._family = socket.getaddrinfo(address[0], address[1])[0][0]
            self._address = address