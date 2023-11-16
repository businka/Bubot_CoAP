__author__ = 'Mikhail Razgovorov'

import asyncio
import logging
import socket

from .endpoint import Endpoint
from ..coap_protocol import CoapProtocol

logger = logging.getLogger(__name__)


class TcpCoapEndpoint(Endpoint):
    """
    Class to handle the EndPoint.
    """
    scheme = 'coap+tcp'

    def __init__(self, **kwargs):
        """
        Data structure that represent a EndPoint
        """
        super().__init__(**kwargs)
        self._pool = set()
        self._sock = None
        self._transport = None
        self._protocol = None
        self._multicast_addresses = None

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

    # @protocol.setter
    # def protocol(self, value):
    #     self._protocol = value

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
        self._sock.sendto(data, address)

    def _init_unicast(self, address):
        self.calc_family_by_address(address)
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

    # async def init_multicast(self, server, address):
    #     self.calc_family_by_address(address)
    #     if self._family == socket.AF_INET:  # IPv4
    #         self.init_multicast_ip4_by_address(address, **self.params)
    #     elif self._family == socket.AF_INET6:  # IPv6
    #         self.init_multicast_ip6_by_address(address, **self.params)
    #     else:
    #         raise NotImplemented(f'Protocol not supported {self._family}')
    #     await self.listen(server)

    def init_unicast_ip4_by_address(self, address, **kwargs):

        self._multicast = None
        self._address = address
        self._family = socket.AF_INET
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(address)
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
        def new_connection(_server, _endpoint):
            connection = protocol_factory(_server, _endpoint, is_server=True)
            self._pool.add(connection)
            return connection

        return await server.loop.create_server(
            lambda: new_connection(server, self),
            self.address[0], self.address[1],
            # sock=self._sock
        )

    async def listen(self, server):
        self._server = await self.create_datagram_endpoint(server, CoapProtocol)
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
        if self._transport:
            self._transport.close()

    async def restart_transport(self, server):
        self.close()
        await self.init_unicast(server, self.address)


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

        print('Send: {!r}'.format(message))
        self.transport.write(data)

        print('Close the client socket')
        self.transport.close()
