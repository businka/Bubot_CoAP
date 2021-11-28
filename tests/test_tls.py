import unittest
from mbed_tls.mbed_tls_datagram_protocol import TlsDatagramProtocol
from src.Bubot_CoAP import SslMsg
import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class TestTslCoap(unittest.TestCase):
    def test_decode_client_hello(self):
        client_hello = b'\x16\xfe\xfd\x00\x00\x00\x00\x00\x00\x00\x02\x00b\x01\x00\x00V\x00\x00\x00\x00\x00\x00\x00V\xfe\xfd`\xc6_,\xdc\x0b&\xcf1L\x98\x15%\xcc\xd6\xf5\xba\xb4\xb5\x93\xd39\rk\xfb\x16l\xf0\xdd\xd9,a\x00\x00\x00\x04\xff\x00\x00\xff\x01\x00\x00(\x00\r\x00\x12\x00\x10\x06\x03\x06\x01\x05\x03\x05\x01\x04\x03\x04\x01\x03\x03\x03\x01\x00\n\x00\x04\x00\x02\x00\x17\x00\x0b\x00\x02\x01\x00\x00\x17\x00\x00'
        answer = b'\x16\xfe\xfd\x00\x00\x00\x00\x00\x00\x00\x02\x00/\x03\x00\x00#\x00\x00\x00\x00\x00\x00\x00#\xfe\xfd `\xcb;0?A\x10\x90\x92i\x84%\xb4\xa2J\xe3\x867A[\xb21/\r\n\xa3N\x18V\xc4s\x95'
        result = None
        protocol = TlsDatagramProtocol(None, None)
        ssl = SslMsg()
        ssl.in_raw = client_hello

        result = protocol.ssl_parse_client_hello(ssl)

        self.assertEqual(result, answer)

    def test_simple_send(self):
        import ssl
        from socket import socket, AF_INET, SOCK_DGRAM
        from dtls import do_patch
        do_patch()
        sock = ssl.wrap_socket(socket(AF_INET, SOCK_DGRAM))
        sock.connect(('192.168.1.13', 20102))
        sock.send('Hi there')

    def test_simpe_server(self):
