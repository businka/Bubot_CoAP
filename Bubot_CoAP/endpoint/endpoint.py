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
        return self._address

    # @address.setter
    # def address(self, value):
    #     self._address = value

    @property
    def family(self):
        return self._family

    async def run(self, server, protocol_factory):
        raise NotImplemented()
