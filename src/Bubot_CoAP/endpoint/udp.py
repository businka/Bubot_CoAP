__author__ = 'Mikhail Razgovorov'

from ..defines import ALL_COAP_NODES, ALL_COAP_NODES_IPV6, COAP_DEFAULT_PORT
from .endpoint import Endpoint
import logging
import socket
import struct

logger = logging.getLogger(__name__)


class UdpCoapEndpoint(Endpoint):
    """
    Class to handle the EndPoint.
    """
    scheme = 'coap'

    def __init__(self, **kwargs):
        """
        Data structure that represent a EndPoint
        """
        super().__init__(**kwargs)
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

    @classmethod
    async def add(cls, endpoint_layer, address, **kwargs):
        result = []
        if address[0] == '' or address[0] is None:
            family = socket.AF_INET
            address = ('', address[1])
        elif address[0] == '::':
            family = socket.AF_INET6
            address = ('[::]', address[1])
        else:
            family = socket.getaddrinfo(address[0], address[1])[0][0]
        multicast = kwargs.get('multicast', False)
        if family == socket.AF_INET:  # IPv4
            result.append(await endpoint_layer.add(cls.init_unicast_ip4_by_address(address, **kwargs)))
            if multicast:
                result.append(await endpoint_layer.add(cls.init_multicast_ip4_by_address(address, **kwargs)))
        elif family == socket.AF_INET6:  # IPv6
            result.append(await endpoint_layer.add(cls.init_unicast_ip6_by_address(address, **kwargs)))
            if multicast:
                result.append(await endpoint_layer.add(cls.init_multicast_ip6_by_address(address, **kwargs)))
        else:
            raise NotImplemented(f'Protocol not supported {family}')
        return result

    def send(self, data, address):
        self._sock.sendto(data, address)

    @classmethod
    def init_unicast_ip4_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.bind(address)
        return self

    @classmethod
    def init_unicast_ip6_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET6
        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(address)
        return self

    @classmethod
    def init_multicast_ip4_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = kwargs.get('multicast_addresses', [ALL_COAP_NODES])
        count_address = len(self._multicast)
        if not count_address:
            raise TypeError('Not defined multicast addresses')
        address = (address[0], kwargs.get('multicast_port', COAP_DEFAULT_PORT))
        self._address = address
        self._family = socket.AF_INET

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(address)
        for group in self._multicast:
            self._sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_pton(socket.AF_INET, group) +
                socket.inet_pton(socket.AF_INET, address[0])
            )
        return self

    @classmethod
    def init_multicast_ip6_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = kwargs.get('multicast_addresses', [ALL_COAP_NODES_IPV6])
        count_address = len(self._multicast)
        if not count_address:
            raise TypeError('Not defined multicast addresses')
        self._family = socket.AF_INET6
        self._address = (address[0], kwargs.get('multicast_port', COAP_DEFAULT_PORT))

        # Bugfix for Python 3.6 for Windows ... missing IPPROTO_IPV6 constant
        if not hasattr(socket, 'IPPROTO_IPV6'):
            socket.IPPROTO_IPV6 = 41

        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._address)
        for group in self._multicast:
            self._sock.setsockopt(
                socket.IPPROTO_IPV6,
                socket.IPV6_JOIN_GROUP,
                socket.inet_pton(socket.AF_INET6, group) +
                struct.pack('i', address[3])
            )
        return self

    async def create_datagram_endpoint(self, server, protocol_factory):
        return await server.loop.create_datagram_endpoint(
            lambda: protocol_factory(server, self), sock=self._sock)

    async def listen(self, server, protocol_factory):
        self._transport, self._protocol = await self.create_datagram_endpoint(server, protocol_factory)
        _address = self._transport.get_extra_info('socket').getsockname()
        source_port = self._address[1]
        if source_port:
            if source_port != _address[1]:
                raise Exception(f'source port {source_port} not installed')
        else:
            self._address = (self._address[0], _address[1])
        logger.debug(f'run {"multicast " if self._multicast else ""}endpoint {_address[0]}:{_address[1]}')
        # _address = socket.getaddrinfo(socket.gethostname(), _address[1], socket.AF_INET, socket.SOCK_DGRAM)[0][4]

    def close(self):
        self._transport.close()
