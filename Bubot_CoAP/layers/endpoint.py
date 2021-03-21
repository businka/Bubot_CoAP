import logging
from Bubot_CoAP.endpoint import Endpoint, supported_scheme
from protocol import CoapProtocol

import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EndpointLayer:
    """
    Class to handle the Endpoint layer
    """

    def __init__(self, server):
        self._server = server
        self.loop = self._server.loop
        self._unicast_endpoints = {}
        self._multicast_endpoints = {}

    @property
    def unicast_endpoints(self):
        return self._unicast_endpoints

    async def add_by_netloc(self, url: str, **kwargs):
        url = urlparse(url)
        try:
            endpoint = supported_scheme[url.scheme]
        except KeyError:
            raise TypeError(f'Unsupported scheme "{url.scheme}"')
        address = (Endpoint.host_port_split(url.netloc))

        multicast = kwargs.get('multicast', False)
        if address[0] == '' or address[0] is None:  # IPv4 default
            family = socket.AF_INET
            # addr_info = socket.getaddrinfo('', address[1], socket.AF_INET)[0]
            # address = addr_info[4]
            address = ('', address[1])
        elif address[0] == '::':
            family = socket.AF_INET6
            # addr_info = socket.getaddrinfo('', address[1], socket.AF_INET6)[0]
            # address = (f'[{addr_info[4][0]}]', addr_info[4][1])
        else:
            addr_info = socket.getaddrinfo(address[0], address[1])[0]
            family = address[0]

        result = []
        if family == socket.AF_INET:  # IPv4
            if multicast:
                result.append(await self.add(endpoint.init_multicast_ip4_by_address(address, **kwargs)))
            result.append(await self.add(endpoint.init_unicast_ip4_by_address(address, **kwargs)))
        elif family == socket.AF_INET6:  # IPv6
            if multicast:
                result.append(await self.add(endpoint.init_multicast_ip6_by_address(address, **kwargs)))
            result.append(await self.add(endpoint.init_unicast_ip6_by_address(address, **kwargs)))
        else:
            raise NotImplemented('Protocol not supported')

    async def add(self, endpoint: Endpoint):
        """
        Handle add endpoint to server

        :type transaction: Transaction
        :param endpoint: the new endpoint
        :rtype : Boolean
        :return:
        """
        if endpoint.multicast:
            key = endpoint.multicast
            if key not in self._multicast_endpoints:
                await endpoint.run(self._server, CoapProtocol)
                self._multicast_endpoints[key] = endpoint
            return self._multicast_endpoints[key]
        else:
            host, port = endpoint.address
            if host not in self._unicast_endpoints:
                self._unicast_endpoints[host] = {}
            if port not in self._unicast_endpoints[host]:
                await endpoint.run(self._server, CoapProtocol)
                self._unicast_endpoints[host][port] = endpoint
            return self._unicast_endpoints[host][port]

    def find_sending_endpoint(self, message):
        dest_address = message.source
        try:
            unicast_endpoints = self._unicast_endpoints[dest_address]
        except KeyError:
            try:
                family = socket.getaddrinfo(dest_address[0], None)[0][0]
                if family == socket.AF_INET:
                    unicast_endpoints = self._unicast_endpoints['']
                elif family == socket.AF_INET6:
                    unicast_endpoints = self._unicast_endpoints['::']
                else:
                    raise TypeError('not endpoint')
            except KeyError:
                raise TypeError('not endpoint')
        try:
            return unicast_endpoints[message.source[1]]
        except KeyError:
            for elem in unicast_endpoints:
                return unicast_endpoints[elem]
        raise TypeError('not endpoint')

    @staticmethod
    def get_key_by_address(address):
        return Endpoint.host_port_join(address[0], address[1])

    def close(self):
        def _close(endpoints):
            _keys = list(endpoints)
            for _key in _keys:
                _ep = endpoints.pop(_key)
                _ep.close()

        _close(self._multicast_endpoints)
        for ip in list(self._unicast_endpoints):
            _close(self._unicast_endpoints.pop(ip))
