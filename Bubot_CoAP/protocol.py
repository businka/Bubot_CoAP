from asyncio import DatagramProtocol
import logging

import logging
import random
import socket
import struct
import threading
import collections

from Bubot_CoAP import defines

from Bubot_CoAP.messages.message import Message
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.response import Response
from Bubot_CoAP.resources.resource import Resource
from Bubot_CoAP.serializer import Serializer

logger = logging.getLogger(__name__)


class CoapProtocol:
    def __init__(self, server, endpoint, **kwargs):
        self.server = server
        self.endpoint = endpoint
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, client_address):
        try:
            client_address = (client_address[0], client_address[1])
            serializer = Serializer()
            message = serializer.deserialize(data, client_address)
            if isinstance(message, int):  # todo переделать в try catch
                return self.datagram_received_bad_message(message, client_address)
            message.destination = self.endpoint.address

            logger.info("receive_datagram - " + str(message))
            if isinstance(message, Request):
                self.datagram_received_request(message)
            elif isinstance(message, Response):
                self.datagram_received_response(message)
            else:  # is Message
                transaction = self.server.messageLayer.receive_empty(message)
                if transaction is not None:
                    with transaction:
                        self.server.blockLayer.receive_empty(message, transaction)
                        self.server.observeLayer.receive_empty(message, transaction)

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
        rst.mid = self.server.messageLayer.fetch_mid()
        rst.source = self.endpoint.address
        self.server.send_datagram(rst)
        return

    def datagram_received_request(self, message):
        transaction = self.server.messageLayer.receive_request(message)
        if transaction.request.duplicated and transaction.completed:
            logger.debug("message duplicated, transaction completed")
            if transaction.response is not None:
                self.server.send_datagram(transaction.response)
            return
        elif transaction.request.duplicated and not transaction.completed:
            logger.debug("message duplicated, transaction NOT completed")
            self.server.send_ack(transaction)
            return
        args = (transaction,)
        t = threading.Thread(target=self.server.receive_request, args=args)
        t.start()
        # self.server.loop.create_task(self.server.receive_request(transaction))
        # self.receive_datagram(data, client_address)

    def datagram_received_response(self, message):
        transaction, send_ack = self.server.messageLayer.receive_response(message)
        if transaction is None:  # pragma: no cover
            return
        self.server._wait_for_retransmit_thread(transaction)
        if send_ack:
            self.server._send_ack(transaction)
        self.server.blockLayer.receive_response(transaction)
        if transaction.block_transfer:
            self.server._send_block_request(transaction)
            return
        elif transaction is None:  # pragma: no cover
            self.server._send_rst(transaction)
            return
        self.server.observeLayer.receive_response(transaction)
        if transaction.notification:  # pragma: no cover
            ack = Message()
            ack.type = defines.Types['ACK']
            ack = self.server.messageLayer.send_empty(transaction, transaction.response, ack)
            self.server.send_datagram(ack)
            self.server.callbackLayer.set_result(transaction.response)
        else:
            self.server.callbackLayer.set_result(transaction.response)
