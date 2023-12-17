__author__ = 'Mikhail Razgovorov'

import asyncio
import logging
import socket
from ..utils import calc_family_by_address
from .endpoint import Endpoint
from ..coap_tcp_protocol import CoapTcpProtocol
from ..utils import str_append_hash
from ..serializer_tcp import SerializerTcp

logger = logging.getLogger(__name__)


class TcpCoapEndpoint(Endpoint):
    """
    Class to handle the EndPoint.
    """
    scheme = 'coap+tcp'
    serializer = SerializerTcp

    def __init__(self, **kwargs):
        """
        Data structure that represent a EndPoint
        """
        super().__init__(**kwargs)
        self.pool = {}
        self._sock = None
        self._transport = None
        self._server = None
        self._protocol = None
        self._multicast_addresses = None
        self._connected = None
        self.destination = None
        self.csm = asyncio.Future()

    def is_closing(self):
        if self.is_client:
            if not self.transport:
                return True
            return self.transport.is_closing()
        else:
            if not self._server:
                return True
            return self._server.is_serving()

    @property
    def sock(self):
        return self._sock

    @property
    def transport(self):
        return self._transport

    # @transport.setter
    # def transport(self, value):
    #     self._transport = value

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        self._protocol = value

    async def start_client(self, server, address):
        self._transport, self._protocol = await server.loop.create_connection(
            lambda: CoapTcpProtocol(server, self),
            address[0], address[1])
        self.csm = await asyncio.wait_for(self.csm, 30)
        self.is_client = True
        self._family, self.destination = calc_family_by_address(address)
        new_address = self.transport.get_extra_info('sockname')
        if self._address and self._address != new_address:
            self._address = new_address
        return self

    @classmethod
    def init_by_socket(cls, sock: socket, is_multicast: bool = False):
        """
        Initialize the endpoint over a ready socket.

        :param sock: socket
        :param is_multicast: if socket is a multicast
        """
        self = cls()
        self._is_multicast = is_multicast
        self._sock = sock
        return self

    def send(self, data, address, **kwargs):
        pool_id = str_append_hash(address[0], address[1])
        protocol = self.pool[pool_id]
        protocol.send(data)

    def _init_unicast(self, address):
        self._family, self._address = calc_family_by_address(address)
        if self._family == socket.AF_INET:  # IPv4
            return self.init_unicast_ip4_by_address(address, **self.params)
        elif self._family == socket.AF_INET6:  # IPv6
            return self.init_unicast_ip6_by_address(address, **self.params)

    async def init_unicast(self, server, address):
        try:
            self._init_unicast(address)
        except Exception as err:
            address = (address[0], 0)  # если порт занят сбрасываем
            self._init_unicast(address)

        await self.listen(server)

    def init_unicast_ip4_by_address(self, address, **kwargs):
        self._address = address
        self._family = socket.AF_INET
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._sock.bind(address)
        # import asyncio
        # loop = asyncio.get_event_loop()
        # loop.create_server()
        return self

    def init_unicast_ip6_by_address(self, address, **kwargs):
        raise NotImplementedError()
        # self._multicast = None
        # self._address = address
        # self._family = socket.AF_INET6
        # self._sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._sock.bind(address)

    async def create_datagram_endpoint(self, server, protocol_factory):
        return await server.loop.create_server(
            lambda: protocol_factory(server, self, is_server=True),
            self.address[0], self.address[1],
            # sock=self._sock
        )

    async def listen(self, server):
        self._server = await self.create_datagram_endpoint(server, CoapTcpProtocol)
        _address = self._server.sockets[0].getsockname()
        source_port = self._address[1]
        if source_port:
            if source_port != _address[1]:
                raise Exception(f'source port {source_port} not installed')
        else:
            self._address = (self._address[0], _address[1])
        logger.debug(f'run {"multicast " if self._multicast else ""}endpoint {_address[0]}:{_address[1]}')
        # _address = socket.getaddrinfo(socket.gethostname(), _address[1], socket.AF_INET, socket.SOCK_DGRAM)[0][4]

    def close(self):
        logger.debug(f'close')
        if self.is_client:
            if self._transport:
                self._transport.close()
            self.pool.pop(str_append_hash(self.address[0], self.address[1]), None)
        else:
            connections = list(self.pool.keys())
            for elem in connections:
                protocol = self.pool.pop(elem, None)
                protocol.close()
            if self._server:
                self._server.close()

    async def restart_transport(self, server):
        self.close()
        await self.init_unicast(server, self.address)

