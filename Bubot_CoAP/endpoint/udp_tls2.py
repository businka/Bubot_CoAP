from Bubot_CoAP.endpoint.udp import UdpCoapEndpoint
import threading
import ssl
import sys
import os
# from dtls import do_patch
from dtls.wrapper import wrap_server, DtlsSocket
import logging
import socket
import struct


# do_patch()


class UdpCoapsEndpoint(UdpCoapEndpoint):
    _scheme = 'coaps'
    ssl_transport = 1  # MBEDTLS_SSL_TRANSPORT_DATAGRAM = DTLS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # self.cert_filename = kwargs['certfile']
            # self.key_filename = kwargs['keyfile']
            pass
        except KeyError as err:
            raise KeyError(f'{err} in CoapEndpoint not defined')

    @classmethod
    def init_unicast_ip4_by_address(cls, address, **kwargs):
        self = cls(**kwargs)
        self._multicast = None
        self._address = address
        self._family = socket.AF_INET

        CERTFILE = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert.pem")
        CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert_ec.pem")
        DH_PARAM = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "dh1024.pem")
        ISSUER_CERTFILE = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert.pem")
        ISSUER_CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert_ec.pem")
        # server_curve = "secp256r1"
        server_curve = "prime256v1"
        self._sock2 = ThreadedEchoServer(
            certificate=CERTFILE_EC,
            ssl_version=ssl.PROTOCOL_DTLSv1_2,
            certreqs=ssl.CERT_NONE,
            cacerts=None,
            dh_param=DH_PARAM,
            ciphers='ALL',
            curves=None,
            sigalgs=None,
            mtu=None,
            server_key_exchange_curve=server_curve,
            server_cert_options=None,
            address=address
        )
        return self

    async def listen(self, server, protocol_factory):
        flag = threading.Event()
        self._sock2.data_handler = protocol_factory
        self._sock2.endpoint = self
        self._sock2.server = server
        self._sock2.start(flag)
        # self.server.join()
        print('start')

    # async def run(self, server, protocol_factory):
    #     # self.ssl_context = ssl.create_default_context()
    #     # self.ssl_context.load_cert_chain(certfile=self.cert_filename, keyfile=self.key_filename)
    #     self._transport, self._protocol = await server.loop.create_datagram_endpoint(
    #         lambda: protocol_factory(server, self), sock=self._sock)
    #     # self._transport = server.loop._make_ssl_transport(self._transport._sock, self._protocol, ssl_context, server_side=True)
    #     # await server.loop.start_tls(self._transport, self._protocol, ssl_context)

    pass


class ThreadedEchoServer(threading.Thread):

    def __init__(self, certificate, ssl_version=None, certreqs=None, cacerts=None,
                 ciphers=None, curves=None, sigalgs=None,
                 mtu=None, server_key_exchange_curve=None, server_cert_options=None,
                 chatty=True, address=None, dh_param=None):

        if ssl_version is None:
            ssl_version = ssl.PROTOCOL_DTLSv1_2
        if certreqs is None:
            certreqs = ssl.CERT_NONE

        self.certificate = certificate
        self.protocol = ssl_version
        self.certreqs = certreqs
        self.cacerts = cacerts
        self.ciphers = ciphers
        self.curves = curves
        self.sigalgs = sigalgs
        self.mtu = mtu
        self.server_key_exchange_curve = server_key_exchange_curve
        self.server_cert_options = server_cert_options
        self.chatty = chatty

        self.data_handler = None
        self.endpoint = None
        self.server = None

        self.flag = None
        self.sock = DtlsSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                               keyfile=self.certificate,
                               certfile=self.certificate,
                               server_side=True,
                               cert_reqs=self.certreqs,
                               ssl_version=self.protocol,
                               ca_certs=self.cacerts,
                               ciphers=self.ciphers,
                               curves=self.curves,
                               sigalgs=self.sigalgs,
                               user_mtu=self.mtu,
                               server_key_exchange_curve=self.server_key_exchange_curve,
                               server_cert_options=self.server_cert_options,
                               )

        if self.chatty:
            sys.stdout.write(' server:  wrapped server socket as %s\n' % str(self.sock))
        self.sock.bind(address)
        self.port = self.sock.getsockname()[1]
        self.active = False
        threading.Thread.__init__(self)
        self.daemon = True

    def start(self, flag=None):
        self.flag = flag
        self.starter = threading.current_thread().ident
        threading.Thread.start(self)

    def run(self):
        self.sock.settimeout(0.05)
        self.sock.listen(0)
        self.active = True
        if self.flag:
            # signal an event
            self.flag.set()
        while self.active:
            try:
                acc_ret = self.sock.recvfrom(4096)
                if acc_ret:
                    # newdata, connaddr = acc_ret
                    handler = self.data_handler(self.server, self.endpoint)
                    handler.datagram_received(*acc_ret)
                    # if self.chatty:
                    #     sys.stdout.write(' server:  new data from ' + str(connaddr) + '\n' + newdata.decode())
                    # self.sock.sendto(newdata.lower(), connaddr)
            except socket.timeout:
                pass
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                if self.chatty:
                    sys.stdout.write(' server:  error ' + str(e) + '\n')
                pass
        if self.chatty:
            sys.stdout.write(' server:  closing socket as %s\n' % str(self.sock))
        self.sock.close()

    def stop(self):
        self.active = False
        if self.starter != threading.current_thread().ident:
            return
        self.join()  # don't allow spawning new handlers after we've checked


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    a = UdpCoapsEndpoint.init_unicast_ip4_by_address(('192.168.1.13', 20102))
    flag = threading.Event()
    # a._sock2.data_handler = protocol_factory
    # a._sock2.server = server
    a._sock2.start(flag)
    a._sock2.join()

    loop.run_until_complete(a.run(None, None))
    loop.run_until_complete(asyncio.sleep(9999))
