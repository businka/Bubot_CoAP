import asyncio
from unittest import IsolatedAsyncioTestCase

from Bubot_CoAP.server import Server
from Bubot_CoAP.coap_protocol import CoapProtocol


class TestTcpServer(IsolatedAsyncioTestCase):
    async def test_1(self):
        host = '192.168.1.11'
        # port = 4777
        port = 0
        server = Server()
        endpoints = await server.add_endpoint(f'coap+tcp://{host}:{port}')
        port = endpoints[0].address[1]
        loop = asyncio.get_running_loop()

        on_con_lost = loop.create_future()
        message = 'Hello World!'

        client = Server()
        transport, protocol = await loop.create_connection(
            lambda: CoapProtocol(client, None),
            host, port)

        # Wait until the protocol signals that the connection
        # is lost and close the transport.
        try:
            await on_con_lost
        finally:
            transport.close()
        ...

