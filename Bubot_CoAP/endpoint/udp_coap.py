__author__ = 'Mikhail Razgovorov'

from urllib.parse import SplitResult
import socket
import struct
import logging
from Bubot_CoAP.defines import ALL_COAP_NODES, ALL_COAP_NODES_IPV6, COAP_DEFAULT_PORT
from Bubot_CoAP.endpoint.endpoint import Endpoint

logger = logging.getLogger(__name__)


class UdpCoapEndpoint(Endpoint):
    """
    Class to handle the EndPoint.
    """
    _scheme = 'coap'

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
        multicast_addresses = kwargs.get('multicast_addresses', [ALL_COAP_NODES])
        count_address = len(multicast_addresses)
        if not count_address:
            raise TypeError('Not defined multicast addresses')
        address = (address[0], kwargs.get('multicast_port', COAP_DEFAULT_PORT))
        self._multicast = f'{self.host_port_join(address)}>{multicast_addresses[0]}{"..." if count_address > 1 else ""}'
        self._address = address
        self._family = socket.AF_INET

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(address)
        for group in multicast_addresses:
            self._sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                struct.pack(
                    "=4sl",
                    socket.inet_aton(group),
                    socket.INADDR_ANY
                )
            )
        return self

    @classmethod
    def init_multicast_ip6_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        multicast_addresses = kwargs.get('multicast_addresses', [ALL_COAP_NODES_IPV6])
        count_address = len(multicast_addresses)
        if not count_address:
            raise TypeError('Not defined multicast addresses')
        address = (address[0], kwargs.get('multicast_port', COAP_DEFAULT_PORT))
        self._multicast = f'{self.host_port_join(address)}>{multicast_addresses[0]}{"..." if count_address > 1 else ""}'
        self._family = socket.AF_INET6
        self._address = address

        # Bugfix for Python 3.6 for Windows ... missing IPPROTO_IPV6 constant
        if not hasattr(socket, 'IPPROTO_IPV6'):
            socket.IPPROTO_IPV6 = 41

        interface_index = 0  # default

        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # sock.setsockopt(41, socket.IPV6_V6ONLY, 0)
        self._sock.bind(address)
        for group in multicast_addresses:
            self._sock.setsockopt(
                socket.IPPROTO_IPV6,
                socket.IPV6_JOIN_GROUP,
                struct.pack(
                    '16si',
                    socket.inet_pton(socket.AF_INET6, group),
                    interface_index
                )
            )
        self._sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        return self

    async def run(self, server, protocol_factory):
        self._transport, self._protocol = await server.loop.create_datagram_endpoint(
            lambda: protocol_factory(server, self), sock=self._sock)

        _address = self._transport.get_extra_info('socket').getsockname()
        source_port = self.address[1]
        if source_port:
            if source_port != _address[1]:
                raise Exception(f'source port {source_port} not installed')
        # self._address = (_address[0], _address[1])
        self._address = (self._address[0], _address[1])
        logger.debug(f'run {"multicast " if self._multicast else ""}endpoint {_address[0]}:{_address[1]}')
        # _address = socket.getaddrinfo(socket.gethostname(), _address[1], socket.AF_INET, socket.SOCK_DGRAM)[0][4]

        # self.unicast_port = _address[1]
        # self.endpoint['IPv6'] = dict(
        #     transport=_transport,
        #     protocol=_protocol,
        #     address=_address,
        #     uri='coap://[{0}]:{1}'.format(_address[0], _address[1])
        # )

    def close(self):
        self._transport.close()
