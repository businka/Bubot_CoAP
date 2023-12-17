import logging

from . import defines
from .messages.message import Message
from .messages.request import Request
from .messages.response import Response

logger = logging.getLogger('Bubot_CoAP')


class CoapProtocol:
    def __init__(self, server, endpoint):
        self.server = server
        self._transport = None
        self.endpoint = endpoint

    def message_received(self, message):
        try:
            logger.debug("Receive message - " + str(message))
            if isinstance(message, Request):
                self.server.loop.create_task(self.datagram_received_request(message))
            elif isinstance(message, Response):
                self.server.loop.create_task(self.datagram_received_response(message))
            elif message.code == defines.Codes.CSM.number:
                csm = dict(
                    max_message_size=message.get_option(defines.OptionRegistry.MAX_MESSAGE_SIZE,
                                                        defines.OptionRegistry.MAX_MESSAGE_SIZE.default)
                )
                self.endpoint.csm.set_result(csm)
                return
            else:  # is Message
                self.server.loop.create_task(self.datagram_received_message(message))

        except RuntimeError:
            logger.exception("Exception with Executor")

    def error_received(self, exc, address=None):
        logger.warning(f'protocol error received {exc}')

        # bug python https://github.com/python/cpython/issues/91227
        from sys import platform
        import asyncio
        if platform.startswith("win"):
            self.server.callback_layer.cancel_waited(asyncio.TimeoutError(str(exc)))
            self.server.loop.create_task(self.endpoint.restart_transport(self.server))
        pass

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
