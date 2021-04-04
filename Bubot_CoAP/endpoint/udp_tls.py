from Bubot_CoAP.endpoint.udp import UdpCoapEndpoint
import ssl


class UdpCoapsEndpoint(UdpCoapEndpoint):
    _scheme = 'coaps'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.cert_filename = kwargs['certfile']
            self.key_filename = kwargs['keyfile']
        except KeyError as err:
            raise KeyError(f'{err} in CoapEndpoint not defined')

    async def run(self, server, protocol_factory):
        await super().run(server, protocol_factory)
        ssl_context = ssl.create_default_context()
        ssl_context.load_cert_chain(certfile=self.cert_filename, keyfile=self.key_filename)
        self._transport = server.loop._make_ssl_transport(self._transport._sock, self._protocol, ssl_context, server_side=True)
        await server.loop.start_tls(self._transport, self._protocol, ssl_context)

    pass
