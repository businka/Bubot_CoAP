from endpoint import UdpCoapEndpoint
import ssl
from dtls import do_patch
import logging
import socket

logger = logging.getLogger(__name__)
do_patch()


class UdpCoapsEndpoint(UdpCoapEndpoint):
    _scheme = 'coaps'
    ssl_transport = 1  # MBEDTLS_SSL_TRANSPORT_DATAGRAM = DTLS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.cert_filename = kwargs['certfile']
            self.key_filename = kwargs['keyfile']
        except KeyError as err:
            raise KeyError(f'{err} in CoapEndpoint not defined')

    @classmethod
    def init_unicast_ip4_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock = ssl.wrap_socket(
            _sock,
            # keyfile=self.key_filename, certfile=self.cert_filename,
            # server_side=True, ssl_version=258
            # ciphers=['TLS_ECDH_ANON_WITH_AES_256_CBC_SHA']
            server_side=True, certfile=self.cert_filename,
            do_handshake_on_connect=False,
            ciphers="NULL"
        )
        self._sock.bind(address)
        return self

    @classmethod
    def init_unicast_ip6_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET6
        _sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock = ssl.wrap_socket(
            _sock,
            # keyfile=self.key_filename, certfile=self.cert_filename,
            server_side=True
        )
        self._sock.bind(address)
        return self

    async def run(self, server, protocol_factory):
        self._transport, self._protocol = await server.loop.create_datagram_endpoint(
            lambda: self.handler(protocol_factory, server, self), sock=self._sock)

        _address = self._transport.get_extra_info('socket').getsockname()
        source_port = self.address[1]
        if source_port:
            if source_port != _address[1]:
                raise Exception(f'source port {source_port} not installed')
        # self._address = (_address[0], _address[1])
        self._address = (self._address[0], _address[1])
        logger.debug(f'run {"multicast " if self._multicast else ""}endpoint {_address[0]}:{_address[1]}')
        # _address = socket.getaddrinfo(socket.gethostname(), _address[1], socket.AF_INET, socket.SOCK_DGRAM)[0][4]

    def handler(server, protocol_factory):
        protocol_factory(server, self)
