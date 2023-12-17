import asyncio
import logging
import socket

logger = logging.getLogger(__name__)


class Endpoint:
    _scheme = None
    serializer = None

    def __init__(self, **kwargs):
        self.params = kwargs
        self._multicast = None
        self._address = None
        self._family = None
        self.is_client = False
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

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def family(self):
        return self._family

    def is_closing(self):
        raise NotImplementedError()

    async def listen(self, server):
        raise NotImplementedError()

    def send(self, data, address, **kwargs):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __del__(self):
        self.close()

    async def restart_transport(self, server):
        raise NotImplementedError()

    async def send_message(self, message, **kwargs):
        message.source = self.address
        logger.debug(f"Send datagram {message}")
        serializer = self.serializer()
        raw_message = serializer.serialize(message)
        self.send(bytes(raw_message), message.destination, **kwargs)
