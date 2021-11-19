from Bubot_CoAP.endpoint.udp import UdpCoapEndpoint
import ssl
from dtls import do_patch
from dtls.wrapper import wrap_server
import logging
import socket
import struct

# from aio_dtls.protocol_dtls import DTLSProtocol


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
    def init_unicast_ip4_by_address(cls, address, *, certificate=None, ssl_version=None, certreqs=None, cacerts=None,
                                    ciphers=None, curves=None, sigalgs=None,
                                    mtu=None, server_key_exchange_curve=None, server_cert_options=None,
                                    chatty=True, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        if ssl_version is None:
            ssl_version = ssl.PROTOCOL_DTLSv1_2
        if certreqs is None:
            certreqs = ssl.CERT_NONE

        import os
        if certificate is None:
            certificate = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert.pem")
            certificate = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "dh1024.pem")
        if certreqs is None:
            certreqs = ssl.CERT_NONE
        if cacerts is None:
            cacerts = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert.pem")

        # CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert_ec.pem")
        # ISSUER_CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert_ec.pem")

        self._sock = wrap_server(socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                                 keyfile=certificate,
                                 certfile=certificate,
                                 cert_reqs=certreqs,
                                 ssl_version=ssl_version,
                                 ca_certs=cacerts,
                                 ciphers=ciphers,
                                 curves=curves,
                                 sigalgs=sigalgs,
                                 user_mtu=mtu,
                                 server_key_exchange_curve=server_key_exchange_curve,
                                 server_cert_options=server_cert_options
                                 )
        # self._sock = ssl.wrap_socket(
        #     _sock,
        #     # keyfile=self.key_filename, certfile=self.cert_filename,
        #     # server_side=True, ssl_version=258
        #     # ciphers=['TLS_ECDH_ANON_WITH_AES_256_CBC_SHA']
        #     server_side=True, certfile=self.cert_filename,
        #     do_handshake_on_connect=False,
        #     ciphers="NULL"
        # )
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

    async def create_datagram_endpoint(self, server, protocol_factory):
        return await server.loop.create_datagram_endpoint(
            lambda: DTLSProtocol(server, server.dtls_connection_manager, self, protocol_factory), sock=self._sock)


if __name__ == '__main__':
    from cryptography.hazmat.primitives.serialization import Encoding
    from cryptography.hazmat.primitives.asymmetric import dh as _dh
    from cryptography.hazmat.backends.interfaces import DHBackend
    from cryptography.hazmat.backends.openssl.backend import backend
    from cryptography.hazmat.primitives.serialization import ParameterFormat


    def generate_diffie_hellman(key_size):
        # "generator is often 2 or 5" / "generator must be 2 or 5.." (depending on where you read)
        DHBackend.generate_dh_parameters(backend, generator=2, key_size=key_size)
        dh_parameters = _dh.generate_parameters(generator=2, key_size=key_size, backend=backend)
        return dh_parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)


    key_size = 256
    with open(f'certs/dh{key_size}.pem', 'wb') as output:
        output.write(generate_diffie_hellman(key_size))
