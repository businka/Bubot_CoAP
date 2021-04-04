from Bubot_CoAP.server import Server
import asyncio
import logging
import cbor2
from Bubot_CoAP import defines
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.option import Option
from Bubot_CoAP.utils import generate_random_token

from Bubot_CoAP.messages.numbers import NON, Code
from Bubot_CoAP.resources.resource import Resource

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class BasicResource(Resource):
    def __init__(self, name="BasicResource", coap_server=None):
        super(BasicResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "Basic Resource"

    async def render_GET_advanced(self, request, response):
        data = {
            "rt": [
                "oic.r.doxm"
            ],
            "if": [
                "oic.if.rw",
                "oic.if.baseline"
            ],
            "p": {
                "bm": 1
            },
            "oxms": [
                0
            ],
            "oxmsel": 0,
            "sct": 1,
            "owned": False,
            "devowneruuid": "00000000-0000-0000-0000-000000000000",
            "deviceuuid": "10000000-0000-0000-0000-000000000001",
            "rowneruuid": "00000000-0000-0000-0000-000000000000"
        }
        option = Option()
        option.number = defines.OptionRegistry.ACCEPT.number
        option.value = 10000
        response.add_option(option)
        response.payload = (10000, cbor2.dumps(data) if data else b'')
        return self, response

    def render_PUT(self, request):
        self.payload = request.payload
        return self

    def render_POST(self, request):
        res = BasicResource()
        res.location_query = request.uri_query
        res.payload = request.payload
        return res

    def render_DELETE(self, request):
        return True


def create_request(sender):
    request = Request()
    request.type = NON
    # request.token = generate_random_token(2)
    request.destination = ('224.0.1.187', 5683)
    # request.destination = (sender, 5683)
    request.multicast = True
    request.source = (sender, None)
    request.code = Code.GET
    request.uri_path = '/oic/sec/doxm'

    option = Option()
    option.number = defines.OptionRegistry.CONTENT_TYPE.number
    option.value = 10000
    request.add_option(option)

    option = Option()
    option.number = defines.OptionRegistry.URI_QUERY.number
    option.value = ''
    request.add_option(option)
    return request


async def get_doxm(server, sender):
    request = create_request(sender)
    result = await server.send_message(request)
    pass


async def main():
    server = Server()
    # await server.add_endpoint('coap://[::]:40401', multicast=True, multicast_addresses=['FF02::158'])
    # await server.add_endpoint('coap://192.168.1.15:40402', multicast=True)
    # await server.add_endpoint('coap://:40405', multicast=True)
    await server.add_endpoint('coap://172.18.59.33:40404', multicast=True)
    await server.add_endpoint('coap://192.168.56.1:40403', multicast=True)
    await server.add_endpoint('coap://192.168.1.15:40401', multicast=True)
    # await asyncio.sleep(100)
    # await server.add_endpoint('coaps://:40402', multicast=True, certfile='iotivitycloud.crt',
    #                           keyfile='iotivitycloud.key')
    server.add_resource('/oic/sec/doxm', BasicResource('test', server))
    # await asyncio.sleep(1)
    print('----')
    await get_doxm(server, '192.168.1.15')
    # await asyncio.sleep(1)
    print('----')
    await get_doxm(server, '172.18.59.33')
    # await asyncio.sleep(1)
    print('----')
    await get_doxm(server, '192.168.56.1')


if __name__ == '__main__':

    from socket import AF_INET6, AF_INET
    import socket
    import struct

    # Bugfix for Python 3.6 for Windows ... missing IPPROTO_IPV6 constant
    if not hasattr(socket, 'IPPROTO_IPV6'):
        socket.IPPROTO_IPV6 = 41

    multicast_address = {
        AF_INET: ["224.0.1.187"],
        AF_INET6: ["FF00::FD"]
    }
    multicast_port = 5683

    addr_info = socket.getaddrinfo('', None)  # get all ip
    for addr in addr_info:
        family = addr[0]
        local_address = addr[4][0]

        sock = socket.socket(family, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((local_address, multicast_port))
        if family == AF_INET:
            for multicast_group in multicast_address[family]:
                sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_ADD_MEMBERSHIP,
                    socket.inet_aton(multicast_group) + socket.inet_aton(local_address)
                )
        elif family == AF_INET6:
            for multicast_group in multicast_address[family]:
                ipv6mr_interface = struct.pack('i', addr[4][3])
                ipv6_mreq = socket.inet_pton(socket.AF_INET6, multicast_group) + ipv6mr_interface
                sock.setsockopt(
                    socket.IPPROTO_IPV6,
                    socket.IPV6_JOIN_GROUP,
                    ipv6_mreq
                )
    # _transport, _protocol = await loop.create_datagram_endpoint(
    #     lambda: protocol_factory(), sock=sock)

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.run_forever()
