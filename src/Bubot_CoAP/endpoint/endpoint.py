import logging

logger = logging.getLogger(__name__)


class Endpoint:
    _scheme = None

    def __init__(self, **kwargs):
        self._multicast = None
        self._address = None
        self._family = None

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

    async def listen(self, server, protocol_factory):
        raise NotImplementedError()

    def send(self, data, address):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __del__(self):
        self.close()
