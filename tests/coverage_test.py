# -*- coding: utf-8 -*-

from queue import Queue
import random
import socket
import asyncio
import logging
import unittest

from Bubot_CoAP.server import Server
from Bubot_CoAP import defines
from Bubot_CoAP.messages.message import Message
from Bubot_CoAP.messages.option import Option
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.response import Response
from Bubot_CoAP.serializer import Serializer

from tests.exampleresources import BasicResource, Long, Separate, Storage, Big, voidResource, XMLResource, ETAGResource, \
    Child, \
    MultipleEncodingResource, AdvancedResource, AdvancedResourceSeparate

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

PAYLOAD = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr,  sed diam nonumy eirmod tempor invidunt ut " \
          "labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et " \
          "ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum " \
          "dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore " \
          "magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. " \
          "Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit " \
          "amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna " \
          "aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita " \
          "kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. " \
          "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore " \
          "eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum " \
          "zzril delenit augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer " \
          "adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. " \
          "Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip " \
          "ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie " \
          "consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim " \
          "qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. " \
          "Nam liber tempor cum soluta nobis eleifend option congue nihil imperdiet doming id quod mazim placerat " \
          "facer possim assum. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh " \
          "euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis " \
          "nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. " \
          "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore " \
          "eu feugiat nulla facilisis. " \
          "At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata " \
          "sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam " \
          "nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et " \
          "accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem " \
          "ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, At accusam aliquyam diam " \
          "diam dolore dolores duo eirmod eos erat, et nonumy sed tempor et et invidunt justo labore Stet clita ea " \
          "et gubergren, kasd magna no rebum. sanctus sea sed takimata ut vero voluptua. est Lorem ipsum dolor " \
          "sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor " \
          "invidunt ut labore et dolore magna aliquyam erat. " \
          "Consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna " \
          "aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita " \
          "kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, " \
          "consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam " \
          "erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd " \
          "gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, " \
          "consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam " \
          "erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd " \
          "gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."

logging.basicConfig(level=logging.DEBUG)


class Tests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.server_address = ("127.0.0.1", 20001)
        self.client_address = ("127.0.0.1", 30001)
        self.current_mid = random.randint(1, 1000)
        self.server_mid = random.randint(1000, 2000)
        self.server = Server()
        await self.server.add_endpoint(f'coap://{self.server_address[0]}:{self.server_address[1]}')
        self.server.add_resource('basic/', BasicResource())
        self.server.add_resource('storage/', Storage())
        self.server.add_resource('separate/', Separate())
        self.server.add_resource('long/', Long())
        self.server.add_resource('big/', Big())
        self.server.add_resource('void/', voidResource())
        self.server.add_resource('xml/', XMLResource())
        self.server.add_resource('encoding/', MultipleEncodingResource())
        self.server.add_resource('etag/', ETAGResource())
        self.server.add_resource('child/', Child())
        self.server.add_resource('advanced/', AdvancedResource())
        self.server.add_resource('advancedSeparate/', AdvancedResourceSeparate())

        # self.server_thread = threading.Thread(target=self.server.listen, args=(1,))
        # self.server_thread.start()
        self.queue = Queue()

    async def asyncTearDown(self) -> None:
        await self.server.close()
        # self.server_thread.join(timeout=25)
        self.server = None

    async def _test_with_client(self, message_list):  # pragma: no cover
        client = Server()
        await client.add_endpoint(f'coap://{self.client_address[0]}:{self.client_address[1]}')
        for message, expected in message_list:
            received_message = Response()
            if message is not None:
                message.destination = self.server_address
                message.source = self.client_address
                received_message: Response = await client.send_message(message)
            if expected is not None:
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type, 'type')
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid, 'mid')
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token, 'token')
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec, f'option {o.name}')
        await client.close()

    async def _test_with_client_observe(self, message_list):  # pragma: no cover
        client = Server()
        await client.add_endpoint(f'coap://{self.client_address[0]}:{self.client_address[1]}')
        for message, expected in message_list:
            if message is not None:
                received_message = await client.send_message(message, self.client_callback)
            await asyncio.sleep(0.1)
            if expected is not None:
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        # client.stop()

    def client_callback(self, response):
        print("Callback")
        self.queue.put(response)

    async def _test_plugtest(self, message_list):  # pragma: no cover
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(self.client_address)
        for message, expected in message_list:
            if message is not None:
                message.source = self.client_address
                datagram = serializer.serialize(message)
                sock.sendto(datagram, message.destination)
            if expected is not None:
                await asyncio.sleep(0.1)
                datagram, source = sock.recvfrom(4096)
                received_message = serializer.deserialize(datagram, source)
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, source)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        sock.close()

    async def _test_datagram(self, message_list):  # pragma: no cover
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram, destination = message
                sock.sendto(datagram, destination)
            if expected is not None:
                await asyncio.sleep(0.1)
                datagram, source = sock.recvfrom(4096)
                received_message = serializer.deserialize(datagram, source)
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, source)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        sock.close()

    async def test_not_allowed(self):
        print("TEST_NOT_ALLOWED")
        path = "/void"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        #  expected.token = None

        exchange1 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        #  expected.token = None

        exchange2 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        #  expected.token = None

        exchange3 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        #  expected.token = None

        exchange4 = (req, expected)

        self.current_mid += 1
        await self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    async def test_separate(self):
        print("TEST_SEPARATE")
        path = "/separate"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.max_age = 60

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"POST"

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.options = None

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"PUT"

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.options = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.DELETED.number
        #  expected.token = None

        exchange4 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    async def test_post(self):
        print("TEST_POST")
        path = "/storage/new_res?id=1"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"test"
        req.add_if_none_match()

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"
        expected.location_query = "id=1"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["test", "not"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"test"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["not"]
        req.payload = b"not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        #  expected.token = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["not"]
        req.payload = b"not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        #  expected.token = None

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = "/storage/new_res"
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_if_none_match()
        req.payload = b"not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        #  expected.token = None

        exchange5 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4, exchange5])

    async def test_post_block(self):
        print("TEST_POST_BLOCK")
        path = "/storage/new_res"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (1, 1, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
        #  expected.token = None
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (0, 1, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (0, 1, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (1, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (1, 1, 64)

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (3, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
        #  expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (2, 0, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange5 = (req, expected)
        self.current_mid += 1

        await self._test_plugtest([exchange1, exchange2, exchange3, exchange4, exchange5])

    async def test_get_block(self):
        print("TEST_GET_BLOCK")
        path = "/big"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        # req.block2 = (0, 0, 512)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, defines.MAX_PAYLOAD)
        expected.size2 = 2041

        exchange0 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (0, 0, 512)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, 512)
        expected.size2 = 2041

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (1, 0, 256)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (1, 1, 256)
        expected.size2 = 2041

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (2, 0, 128)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (2, 1, 128)
        expected.size2 = 2041

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (3, 0, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (3, 1, 64)
        expected.size2 = 2041

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (4, 0, 32)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (4, 1, 32)
        expected.size2 = 2041

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (5, 0, 16)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (5, 1, 16)
        expected.size2 = 2041

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (6, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (6, 0, 1024)
        expected.size2 = 2041

        exchange7 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (7, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.block2 = (7, 0, 1024)
        expected.size2 = 2041

        exchange8 = (req, expected)
        self.current_mid += 1

        await self._test_plugtest([exchange0, exchange1, exchange2, exchange3, exchange4,
                             exchange5, exchange6, exchange7, exchange8])

    async def test_post_block_big(self):
        print("TEST_POST_BLOCK_BIG")
        path = "/big"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (0, 1, 16)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (0, 1, 16)

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (1, 1, 32)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (1, 1, 32)

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (2, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (2, 1, 64)

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (3, 1, 128)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (3, 1, 128)

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (4, 1, 256)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (4, 1, 256)

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (5, 1, 512)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        #  expected.token = None
        expected.payload = None
        expected.block1 = (5, 1, 512)

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = PAYLOAD
        req.block1 = (6, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None

        exchange7 = (req, expected)
        self.current_mid += 1

        await self._test_plugtest([exchange1, exchange2, exchange3, exchange4, exchange5, exchange6, exchange7])

    async def test_options(self):
        print("TEST_OPTIONS")
        path = "/storage/new_res"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        req.del_option(option)
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        req.del_option_by_name("ETag")
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        del req.etag
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange3 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3])

    async def test_long_options(self):
        """
        Test processing of options with extended length
        """
        print("TEST_LONG_OPTIONS")
        path = "/storage/"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        # This option should be silently ignored by the server
        # since it is not critical
        option.number = defines.OptionRegistry.RM_MESSAGE_SWITCHING.number
        option.value = b'\1\1\1\1\0\0'
        req.add_option(option)
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1])

        # This option (244) should be silently ignored by the server
        req = (b'\x40\x01\x01\x01\xd6\xe7\x01\x01\x01\x01\x00\x00', self.server_address)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.NOT_FOUND.number
        #  expected.token = None
        expected.payload = None

        exchange21 = (req, expected)
        self.current_mid += 1

        # This option (245) should cause BAD REQUEST, as unrecognizable critical
        req = (b'\x40\x01\x01\x01\xd6\xe8\x01\x01\x01\x01\x00\x00', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange22 = (req, expected)
        self.current_mid += 1

        # This option (65525) should cause BAD REQUEST, as unrecognizable critical
        req = (b'\x40\x01\x01\x01\xe6\xfe\xe8\x01\x01\x01\x01\x00\x00', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange23 = (req, expected)
        self.current_mid += 1

        await self._test_datagram([exchange21, exchange22, exchange23])

    async def test_content_type(self):
        print("TEST_CONTENT_TYPE")
        path = "/storage/new_res"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"<value>test</value>"
        req.content_type = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"Basic Resource"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"test"

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"<value>test</value>"
        expected.content_type = defines.Content_types["application/xml"]

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/json"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_ACCEPTABLE.number
        #  expected.token = None
        expected.payload = None

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/xml"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"<value>0</value>"

        print(expected.pretty_print())

        exchange7 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"0"

        exchange8 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"<value>0</value>"
        expected.content_type = defines.Content_types["application/xml"]

        exchange9 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/json"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"{'value': '0'}"
        expected.content_type = defines.Content_types["application/json"]

        exchange10 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4, exchange5,
                                exchange6, exchange7, exchange8, exchange9, exchange10])

    async def test_ETAG(self):
        print("TEST_ETAG")
        path = "/etag"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.token = None
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = req.token
        expected.payload = b"ETag resource"
        expected.etag = bytes("0", "utf-8")

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None
        expected.etag = "1"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.etag = bytes("1", "utf-8")

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.VALID.number
        #  expected.token = None
        expected.payload = b"test"
        expected.etag = bytes("1", "utf-8")

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"echo payload"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    async def test_child(self):
        print("TEST_CHILD")
        path = "/child"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        #  expected.token = None
        expected.payload = None
        expected.location_path = "child"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = b"test"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"testPUT"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.DELETED.number
        #  expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    async def test_not_found(self):
        print("TEST_not_found")
        path = "/not_found"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.token = 100

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = 100
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        #  expected.token = None

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = b"testPUT"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        #  expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        #  expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    async def test_invalid(self):
        print("TEST_INVALID")

        # version
        req = (b'\x00\x01\x8c\xda', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange1 = (req, expected)

        # version
        req = (b'\x40', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange2 = (req, expected)

        # code
        req = (b'\x40\x05\x8c\xda', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange3 = (req, expected)

        # option
        req = (b'\x40\x01\x8c\xda\x94', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange4 = (req, expected)

        # payload marker
        req = (b'\x40\x02\x8c\xda\x75\x62\x61\x73\x69\x63\xff', self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange5 = (req, expected)

        await self._test_datagram([exchange1, exchange2, exchange3, exchange4, exchange5])

    async def test_post_block_big_client(self):
        print("TEST_POST_BLOCK_BIG_CLIENT")
        path = "/big"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras sollicitudin fermentum ornare. " \
                      "Cras accumsan tellus quis dui lacinia eleifend. Proin ultrices rutrum orci vitae luctus. " \
                      "Nullam malesuada pretium elit, at aliquam odio vehicula in. Etiam nec maximus elit. " \
                      "Etiam at erat ac ex ornare feugiat. Curabitur sed malesuada orci, id aliquet nunc. Phasellus " \
                      "nec leo luctus, blandit lorem sit amet, interdum metus. Duis efficitur volutpat magna, ac " \
                      "ultricies nibh aliquet sit amet. Etiam tempor egestas augue in hendrerit. Nunc eget augue " \
                      "ultricies, dignissim lacus et, vulputate dolor. Nulla eros odio, fringilla vel massa ut, " \
                      "facilisis cursus quam. Fusce faucibus lobortis congue. Fusce consectetur porta neque, id " \
                      "sollicitudin velit maximus eu. Sed pharetra leo quam, vel finibus turpis cursus ac. " \
                      "Aenean ac nisi massa. Cras commodo arcu nec ante tristique ullamcorper. Quisque eu hendrerit" \
                      " urna. Cras fringilla eros ut nunc maximus, non porta nisl mollis. Aliquam in rutrum massa." \
                      " Praesent tristique turpis dui, at ultricies lorem fermentum at. Vivamus sit amet ornare neque, " \
                      "a imperdiet nisl. Quisque a iaculis libero, id tempus lacus. Aenean convallis est non justo " \
                      "consectetur, a hendrerit enim consequat. In accumsan ante a egestas luctus. Etiam quis neque " \
                      "nec eros vestibulum faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci " \
                      "enim, ultrices a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum." \
                      "Vivamus ut odio ac odio malesuada accumsan. Aenean vehicula diam at tempus ornare. Phasellus " \
                      "dictum mauris a mi consequat, vitae mattis nulla fringilla. Ut laoreet tellus in nisl efficitur," \
                      " a luctus justo tempus. Fusce finibus libero eget velit finibus iaculis. Morbi rhoncus purus " \
                      "vel vestibulum ullamcorper. Sed ac metus in urna fermentum feugiat. Nulla nunc diam, sodales " \
                      "aliquam mi id, varius porta nisl. Praesent vel nibh ac turpis rutrum laoreet at non odio. " \
                      "Phasellus ut posuere mi. Suspendisse malesuada velit nec mauris convallis porta. Vivamus " \
                      "sed ultrices sapien, at cras amet.".encode()

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        #  expected.token = None
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        await self._test_with_client([exchange1])

    async def test_observe_client(self):
        print("TEST_OBSERVE_CLIENT")
        path = "/basic"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        #  expected.token = None
        expected.payload = None
        expected.observe = 1

        exchange1 = (req, expected)

        req = Message()
        req.code = defines.Codes.EMPTY.number
        req.uri_path = path
        req.type = defines.Types["RST"]
        req._mid = self.current_mid
        req.destination = self.server_address

        exchange2 = (req, None)
        self.current_mid += 1

        await self._test_with_client_observe([exchange1, exchange2])


if __name__ == '__main__':
    unittest.main()
