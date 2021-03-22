import logging
from Bubot_CoAP.endpoint import Endpoint, supported_scheme
from Bubot_CoAP.utils import parse_uri2
from Bubot_CoAP.protocol import CoapProtocol


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

    async def add_by_netloc(self, uri: str, **kwargs):
        _uri = parse_uri2(uri)
        try:
            endpoint = supported_scheme[_uri['scheme']]
        except KeyError:
            raise TypeError(f'Unsupported scheme \'{_uri["scheme"]}\'')
        address = _uri['address']

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
            family = addr_info[0]

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
            raise NotImplemented(f'Protocol not supported {family}')
        return result

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
            scheme = endpoint.scheme
            family = endpoint.family
            host, port = endpoint.address
            if scheme not in self._unicast_endpoints:
                self._unicast_endpoints[scheme] = {'default': endpoint}
            if family not in self._unicast_endpoints[scheme]:
                self._unicast_endpoints[scheme][family] = {'default': endpoint}
            if host not in self._unicast_endpoints[scheme][family]:
                self._unicast_endpoints[scheme][family][host] = {'default': endpoint}
            if port not in self._unicast_endpoints[scheme][family][host]:
                self._unicast_endpoints[scheme][family][host][port] = endpoint
                await endpoint.run(self._server, CoapProtocol)
            return endpoint

    def find_sending_endpoint(self, message):
        source_address = message.source
        scheme = message.scheme
        dest_address = message.destination
        if source_address:
            return self._unicast_endpoints[message.scheme][message.family][source_address[0]][source_address[1]]
        else:
            family = socket.getaddrinfo(dest_address[0], None)[0][0]
            return self._unicast_endpoints[scheme][family]['default']

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
        for scheme in list(self._unicast_endpoints):
            self._unicast_endpoints[scheme].pop('default')
            for family in list(self._unicast_endpoints[scheme]):
                self._unicast_endpoints[scheme][family].pop('default')
                for ip in list(self._unicast_endpoints[scheme][family]):
                    _close(self._unicast_endpoints[scheme][family].pop(ip))
                del self._unicast_endpoints[scheme][family]
            del self._unicast_endpoints[scheme]
