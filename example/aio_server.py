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

    def render_GET_advanced(self, request, response):
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


def create_request():
    request = Request()
    request.type = NON
    # request.token = generate_random_token(2)
    request.destination = ('192.168.1.18', 62015)
    request.source = ('192.168.1.15', None)
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


async def get_doxm(server):
    request = create_request()
    result = await server.send_message(request)
    pass


async def main():
    server = Server()
    # await server.add_endpoint('coap://[::]:40401', multicast=True, multicast_addresses=['FF02::158'])
    await server.add_endpoint('coap://:40401', multicast=True)
    # await server.add_endpoint('coaps://:40402', multicast=True, certfile='iotivitycloud.crt',
    #                           keyfile='iotivitycloud.key')
    server.add_resource('/oic/sec/doxm', BasicResource('test', server))

    await get_doxm(server)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
