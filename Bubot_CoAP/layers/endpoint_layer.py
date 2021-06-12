import logging
from Bubot_CoAP.endpoint import Endpoint, supported_scheme
from Bubot_CoAP.utils import parse_uri2
from Bubot_CoAP.protocol import CoapProtocol

import socket

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
        async def add_all_address(_family, _result):
            addr_info = socket.getaddrinfo('', address[1], _family)
            _new_port = None
            for addr in addr_info:
                if _new_port:
                    if _family == socket.AF_INET:
                        _address = (addr[4][0], _new_port)
                    elif _family == socket.AF_INET6:
                        _address = (addr[4][0], _new_port, addr[4][2], addr[4][3])
                    else:
                        raise NotImplemented()
                else:
                    _address = addr[4]
                res = await endpoint.add(self, _address, **kwargs)
                if not addr[1] and not _new_port:  # if port not defined. set the same
                    _new_port = res[0].address[1]

                _result += res

        _uri = parse_uri2(uri)
        try:
            endpoint = supported_scheme[_uri['scheme']]
        except KeyError:
            raise TypeError(f'Unsupported scheme \'{_uri["scheme"]}\'')
        address = _uri['address']
        result = []

        # multicast = kwargs.get('multicast', False)
        if address[0] == '' or address[0] is None:  # IPv4 default
            await add_all_address(socket.AF_INET, result)
        elif address[0] == '::':
            await add_all_address(socket.AF_INET6, result)
        else:
            result += await endpoint.add(self, address, **kwargs)
        return result

    async def add(self, endpoint: Endpoint):
        """
        Handle add endpoint to server

        :type endpoint: Endpoint
        :param endpoint: the new endpoint
        :rtype : Boolean
        :return:
        """
        scheme = endpoint.scheme
        family = endpoint.family
        await endpoint.run(self._server, CoapProtocol)
        host, port = endpoint.address
        _endpoints = self._multicast_endpoints if endpoint.multicast else self._unicast_endpoints
        if scheme not in _endpoints:
            _endpoints[scheme] = {}
        if family not in _endpoints[scheme]:
            _endpoints[scheme][family] = {}
        if endpoint.multicast:
            if host not in _endpoints[scheme][family]:
                _endpoints[scheme][family][host] = endpoint
                return endpoint
        else:
            if host not in _endpoints[scheme][family]:
                _endpoints[scheme][family][host] = {}  # 'default': endpoint}
                if port not in self._unicast_endpoints[scheme][family][host]:
                    self._unicast_endpoints[scheme][family][host][port] = endpoint
                return endpoint
        return None

    def find_sending_endpoint(self, message):
        source_address = message.source
        scheme = message.scheme
        dest_address = message.destination
        family = socket.getaddrinfo(dest_address[0], None)[0][0]
        if source_address:
            _tmp = self.unicast_endpoints[scheme][family][source_address[0]]
            if source_address[1] is None:
                return _tmp[list(_tmp.keys())[0]]
            return _tmp.get(source_address[1])
        raise Exception('source address not defined')
        # else:
        # return self._unicast_endpoints[scheme][family]['default']

    def close(self):
        def _close(endpoints):
            _keys = list(endpoints)
            for _key in _keys:
                _ep = endpoints.pop(_key)
                _ep.close()

        for scheme in list(self._unicast_endpoints):
            for family in list(self._unicast_endpoints[scheme]):
                for ip in list(self._unicast_endpoints[scheme][family]):
                    _close(self._unicast_endpoints[scheme][family].pop(ip))
                del self._unicast_endpoints[scheme][family]
            del self._unicast_endpoints[scheme]

        for scheme in list(self._multicast_endpoints):
            for family in list(self._multicast_endpoints[scheme]):
                _close(self._multicast_endpoints[scheme].pop(family))
            del self._multicast_endpoints[scheme]
