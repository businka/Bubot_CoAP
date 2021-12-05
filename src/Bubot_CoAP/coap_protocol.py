from asyncio import DatagramProtocol
import logging

from . import defines

from .messages.message import Message
from .messages.request import Request
from .messages.response import Response
from .serializer import Serializer

logger = logging.getLogger(__name__)


class CoapProtocol(DatagramProtocol):
    def __init__(self, server, endpoint, **kwargs):
        self.server = server
        self.endpoint = endpoint

    def datagram_received(self, data, client_address):
        try:
            client_address = (client_address[0], client_address[1])
            serializer = Serializer()
            message = serializer.deserialize(data, client_address)

            if isinstance(message, int):  # todo переделать в try catch
                # if data[0] == b'\x16':  # client hello
                return self.datagram_received_bad_message(message, client_address)

            message.destination = self.endpoint.address
            message.multicast = bool(self.endpoint.multicast)
            message.scheme = self.endpoint.scheme
            message.family = self.endpoint.family

            logger.debug("receive_datagram - " + str(message))
            if isinstance(message, Request):
                self.server.loop.create_task(self.datagram_received_request(message))
            elif isinstance(message, Response):
                self.server.loop.create_task(self.datagram_received_response(message))
            else:  # is Message
                self.server.loop.create_task(self.datagram_received_message(message))

        except RuntimeError:
            logger.exception("Exception with Executor")

    def error_received(self, exc):
        logger.error(f'protocol error received {str(exc)}')
        pass

    def datagram_received_bad_message(self, message, client_address):
        logger.error("receive_datagram - BAD REQUEST")

        rst = Message()
        rst.destination = client_address
        rst.type = defines.Types["RST"]
        rst.code = message
        rst.mid = self.server.message_layer.fetch_mid()
        rst.source = self.endpoint.address
        self.server.send_datagram(rst)
        return

    async def datagram_received_request(self, message):
        transaction = await self.server.message_layer.receive_request(message)
        if transaction.request.duplicated and transaction.completed:
            logger.debug("message duplicated, transaction completed")
            if transaction.response is not None:
                self.server.send_datagram(transaction.response)
            return
        elif transaction.request.duplicated and not transaction.completed:
            logger.debug("message duplicated, transaction NOT completed")
            await self.server.send_ack(transaction)
            return
        await self.server.receive_request(transaction)

    async def datagram_received_response(self, message):
        transaction, send_ack = self.server.message_layer.receive_response(message)
        if transaction is None:  # pragma: no cover
            return
        await self.server.wait_for_retransmit_thread(transaction)
        if send_ack:
            await self.server.send_ack(transaction, transaction.response)
        self.server.block_layer.receive_response(transaction)
        if transaction.block_transfer:
            await self.server.send_block_request(transaction)
            return
        elif transaction is None:  # pragma: no cover
            self.server._send_rst(transaction)
            return
        self.server.observe_layer.receive_response(transaction)
        if transaction.notification:  # pragma: no cover
            ack = Message()
            ack.type = defines.Types['ACK']
            ack = self.server.message_layer.send_empty(transaction, transaction.response, ack)
            self.server.send_datagram(ack)
            self.server.callback_layer.set_result(transaction.response)
        else:
            self.server.callback_layer.set_result(transaction.response)

    async def datagram_received_message(self, message):
        transaction = self.server.message_layer.receive_empty(message)
        if transaction is not None:
            async with transaction.lock:
                self.server.block_layer.receive_empty(message, transaction)
                self.server.observe_layer.receive_empty(message, transaction)
