from server import Server
import asyncio
import logging
import cbor2
import defines
from messages.request import Request
from messages.option import Option

from messages.numbers import NON, Code
from resources.resource import Resource

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


def create_request_get_doxm(sender, destination):
    request = Request()
    request.type = NON
    # request.token = generate_random_token(2)
    request.destination = destination
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


def create_request_get_res(sender, destination):
    request = Request()
    request.type = NON
    request.scheme = 'coaps'
    # request.token = generate_random_token(2)
    request.destination = destination
    # request.destination = (sender, 5683)
    # request.multicast = True
    request.source = sender
    request.code = Code.GET
    request.uri_path = '/oic/res'

    option = Option()
    option.number = defines.OptionRegistry.CONTENT_TYPE.number
    option.value = 10000
    request.add_option(option)

    option = Option()
    option.number = defines.OptionRegistry.URI_QUERY.number
    option.value = ''
    request.add_option(option)
    return request


async def get_doxm(server, sender, destination):
    request = create_request_get_doxm(sender, destination)
    return await server.send_message(request)


async def get_ioc_res(server, sender, destination):
    request = create_request_get_res(sender, destination)
    return await server.send_message(request)


async def main():
    server = Server()
    # await server.add_endpoint('coap://[::]:40401', multicast=True, multicast_addresses=['FF02::158'])
    # await server.add_endpoint('coap://192.168.1.15:40402', multicast=True)
    # await server.add_endpoint('coap://:40405', multicast=True)
    # await server.add_endpoint('coap://172.18.59.33:40404', multicast=True)
    # await server.add_endpoint('coap://192.168.56.1:40403', multicast=True)
    # await server.add_endpoint('coap://192.168.1.15:40401', multicast=True)
    # await asyncio.sleep(100)
    await server.add_endpoint('coaps://[::]:40402', certfile='iotivitycloud.crt',
                              keyfile='iotivitycloud.key')
    # server.add_resource('/oic/sec/doxm', BasicResource('test', server))
    # await asyncio.sleep(1)
    print('----')

    res = await get_ioc_res(server, ('fe80::240a:dd92:e22a:c2c4', 40402), ('fe80::240a:dd92:e22a:c2c4', 50201))
    pass
    # await get_doxm(server, '192.168.1.15')
    # # await asyncio.sleep(1)
    # print('----')
    # await get_doxm(server, '172.18.59.33')
    # # await asyncio.sleep(1)
    # print('----')
    # await get_doxm(server, '192.168.56.1')

    a = {'rel': ['self'], 'anchor': 'ocf://849ea6ed-50ff-4d56-43ab-2708ab09b50d', 'href': '/oic/res',
         'rt': ['oic.wk.res'], 'if': ['oic.if.ll', 'oic.if.baseline'], 'p': {'bm': 1},
         'eps': [{'ep': 'coap://[fe80::240a:dd92:e22a:c2c4]:50200', 'lat': 240},
                 {'ep': 'coaps://[fe80::240a:dd92:e22a:c2c4]:50201', 'lat': 240},
                 {'ep': 'coap+tcp://[fe80::240a:dd92:e22a:c2c4]:58011', 'lat': 240},
                 {'ep': 'coaps+tcp://[fe80::240a:dd92:e22a:c2c4]:58012', 'lat': 240}]}


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
