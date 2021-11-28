# -*- coding: utf-8 -*-

# Test the support for DTLS through the SSL module. Adapted from the Python
# standard library's test_ssl.py regression test module by Björn Freise.

import sys

my_stdout = sys.stdout
import unittest
import threading
import sys
import socket
import os
import pprint

import logging

_logger = logging.getLogger(__name__)

import ssl
from dtls.wrapper import DtlsSocket
from dtls import err, force_routing_demux

# force_routing_demux()


HOST = "localhost"
CHATTY = True
CHATTY_CLIENT = True


class ThreadedEchoServer(threading.Thread):

    def __init__(self, certificate, ssl_version=None, certreqs=None, cacerts=None,
                 ciphers=None, curves=None, sigalgs=None,
                 mtu=None, server_key_exchange_curve=None, server_cert_options=None,
                 chatty=True, address=None):

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
                               server_cert_options=self.server_cert_options
                               )

        if self.chatty:
            sys.stdout.write(' server:  wrapped server socket as %s\n' % str(address))
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
                    newdata, connaddr = acc_ret
                    if self.chatty:
                        sys.stdout.write(' server:  new data from ' + str(connaddr) + '\n' + newdata.decode())
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
    CERTFILE = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert.pem")
    CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "keycert_ec.pem")
    ISSUER_CERTFILE = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert.pem")
    ISSUER_CERTFILE_EC = os.path.join(os.path.dirname(__file__) or os.curdir, "certs", "ca-cert_ec.pem")
    chatty, connectionchatty = CHATTY, CHATTY_CLIENT
    server = ThreadedEchoServer(certificate=CERTFILE,
                                ssl_version=ssl.PROTOCOL_DTLSv1_2,
                                certreqs=ssl.CERT_NONE,
                                cacerts=ISSUER_CERTFILE,
                                ciphers=None,
                                curves=None,
                                sigalgs=None,
                                mtu=None,
                                server_key_exchange_curve=None,
                                server_cert_options=None,
                                chatty=chatty,
                                address=('192.168.1.13', 20102)
                                )
    flag = threading.Event()
    server.start(flag)
    server.join()
