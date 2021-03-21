import time
import logging
import asyncio
import random
import socket
import struct
import threading
import collections
from urllib.parse import urlparse

from Bubot_CoAP import defines
from Bubot_CoAP.layers.blocklayer import BlockLayer
from Bubot_CoAP.layers.messagelayer import MessageLayer
from Bubot_CoAP.layers.observelayer import ObserveLayer
from Bubot_CoAP.layers.requestlayer import RequestLayer
from Bubot_CoAP.layers.resourcelayer import ResourceLayer
from Bubot_CoAP.layers.callback import CallbackLayer
from Bubot_CoAP.messages.message import Message
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.response import Response
from Bubot_CoAP.resources.resource import Resource
from Bubot_CoAP.serializer import Serializer
from Bubot_CoAP.utils import Tree
from Bubot_CoAP.layers.endpoint import EndpointLayer
from Bubot_CoAP.endpoint import Endpoint, supported_scheme

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class Server:
    """
    Implementation of the CoAP server
    """

    def __init__(self, starting_mid=None, cb_ignore_listen_exception=None, **kwargs):
        """
        Initialize the server.

        :param starting_mid: used for testing purposes
        :param cb_ignore_listen_exception: Callback function to handle exception raised during the socket listen operation
        """

        self.loop = kwargs.get('loop', asyncio.get_event_loop())

        # self.stopped = threading.Event()
        # self.stopped.clear()
        self.to_be_stopped = []
        # self.purge = threading.Thread(target=self.purge)
        # self.purge.start()
        self.endpointLayer = EndpointLayer(self)
        self.messageLayer = MessageLayer(starting_mid)
        self.blockLayer = BlockLayer()
        self.observeLayer = ObserveLayer()
        self.requestLayer = RequestLayer(self)
        self.resourceLayer = ResourceLayer(self)
        self.callbackLayer = CallbackLayer()
        # Resource directory
        root = Resource('root', self, visible=False, observable=False, allow_children=False)
        root.path = '/'
        self.root = Tree()
        self.root["/"] = root
        self._serializer = None
        self._cb_ignore_listen_exception = cb_ignore_listen_exception

    def purge(self):
        """
        Clean old transactions

        """
        while not self.stopped.isSet():
            self.stopped.wait(timeout=defines.EXCHANGE_LIFETIME)
            self.messageLayer.purge()

    async def close(self):
        """
        Stop the server.

        """
        logger.info("Stop server")
        # self.stopped.set()
        # for event in self.to_be_stopped:
        #     event.set()
        self.endpointLayer.close()

    def receive_request(self, transaction):
        """
        Handle requests coming from the udp socket.

        :param transaction: the transaction created to manage the request
        """

        with transaction:

            transaction.separate_timer = self._start_separate_timer(transaction)

            self.blockLayer.receive_request(transaction)

            if transaction.block_transfer:
                self._stop_separate_timer(transaction.separate_timer)
                self.messageLayer.send_response(transaction)
                self.send_datagram(transaction.response)
                return

            self.observeLayer.receive_request(transaction)

            self.requestLayer.receive_request(transaction)

            if transaction.resource is not None and transaction.resource.changed:
                self.notify(transaction.resource)
                transaction.resource.changed = False
            elif transaction.resource is not None and transaction.resource.deleted:
                self.notify(transaction.resource)
                transaction.resource.deleted = False

            self.observeLayer.send_response(transaction)

            self.blockLayer.send_response(transaction)

            self._stop_separate_timer(transaction.separate_timer)

            self.messageLayer.send_response(transaction)

            if transaction.response is not None:
                if transaction.response.type == defines.Types["CON"]:
                    self._start_retransmission(transaction, transaction.response)
                self.send_datagram(transaction.response)

    async def send_message(self, message, no_response=False):
        if isinstance(message, Request):
            request = self.requestLayer.send_request(message)
            request = self.observeLayer.send_request(request)
            request = self.blockLayer.send_request(request)
            if no_response:
                # don't add the send message to the message layer transactions
                self.send_datagram(request)
                return
            transaction = self.messageLayer.send_request(request)
            self.send_datagram(transaction.request)
            if transaction.request.type == defines.Types["CON"]:
                self._start_retransmission(transaction, transaction.request)
            return await self.callbackLayer.wait(request)
        elif isinstance(message, Message):
            message = self.observeLayer.send_empty(message)
            message = self.messageLayer.send_empty(None, None, message)
            self.send_datagram(message)

    def send_datagram(self, message):
        """
        Send a message through the udp socket.

        :type message: Message
        :param message: the message to send
        """
        # if not self.stopped.isSet():
        # host, port = message.destination
        # host, port = message.source
        endpoint = self.endpointLayer.find_sending_endpoint(message)
        message.source = endpoint.address
        logger.info("send_datagram - " + str(message))
        serializer = Serializer()
        raw_message = serializer.serialize(message)
        endpoint.sock.sendto(raw_message, message.destination)

    def add_resource(self, path, resource):
        """
        Helper function to add resources to the resource directory during server initialization.

        :param path: the path for the new created resource
        :type resource: Resource
        :param resource: the resource to be added
        """

        assert isinstance(resource, Resource)
        path = path.strip("/")
        paths = path.split("/")
        actual_path = ""
        i = 0
        for p in paths:
            i += 1
            actual_path += "/" + p
            try:
                res = self.root[actual_path]
            except KeyError:
                res = None
            if res is None:
                resource.path = actual_path
                self.root[actual_path] = resource
        return True

    def remove_resource(self, path):
        """
        Helper function to remove resources.

        :param path: the path for the unwanted resource
        :rtype : the removed object
        """

        path = path.strip("/")
        paths = path.split("/")
        actual_path = ""
        i = 0
        for p in paths:
            i += 1
            actual_path += "/" + p
        try:
            res = self.root[actual_path]
        except KeyError:
            res = None
        if res is not None:
            del (self.root[actual_path])
        return res

    async def add_endpoint(self, url: str, **kwargs):
        """
        Helper function to add endpoint to the endpoint directory during server initialization.

        :param endpoint: the endpoint to be added
        """
        return await self.endpointLayer.add_by_netloc(url, **kwargs)

    def remove_endpoint(self, **kwargs):
        return self.endpointLayer.remove(**kwargs)
        pass

    @staticmethod
    def _wait_for_retransmit_thread(transaction):
        """
        Only one retransmit thread at a time, wait for other to finish

        """
        if hasattr(transaction, 'retransmit_thread'):
            while transaction.retransmit_thread is not None:
                logger.debug("Waiting for retransmit thread to finish ...")
                time.sleep(0.01)
                continue

    def _start_retransmission(self, transaction, message):
        """
        Start the retransmission task.

        :type transaction: Transaction
        :param transaction: the transaction that owns the message that needs retransmission
        :type message: Message
        :param message: the message that needs the retransmission task
        """
        with transaction:
            if message.type == defines.Types['CON']:
                future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
                transaction.retransmit_thread = threading.Thread(target=self._retransmit,
                                                                 args=(transaction, message, future_time, 0))
                transaction.retransmit_stop = threading.Event()
                self.to_be_stopped.append(transaction.retransmit_stop)
                transaction.retransmit_thread.start()

    def _retransmit(self, transaction, message, future_time, retransmit_count):
        """
        Thread function to retransmit the message in the future

        :param transaction: the transaction that owns the message that needs retransmission
        :param message: the message that needs the retransmission task
        :param future_time: the amount of time to wait before a new attempt
        :param retransmit_count: the number of retransmissions
        """
        with transaction:
            while retransmit_count < defines.MAX_RETRANSMIT and (not message.acknowledged and not message.rejected) \
                    and not self.stopped.isSet():
                if transaction.retransmit_stop is not None:
                    transaction.retransmit_stop.wait(timeout=future_time)
                if not message.acknowledged and not message.rejected and not self.stopped.isSet():
                    retransmit_count += 1
                    future_time *= 2
                    self.send_datagram(message)

            if message.acknowledged or message.rejected:
                message.timeouted = False
            else:
                logger.warning("Give up on message {message}".format(message=message.line_print))
                message.timeouted = True
                if message.observe is not None:
                    self.observeLayer.remove_subscriber(message)

            try:
                self.to_be_stopped.remove(transaction.retransmit_stop)
            except ValueError:
                pass
            transaction.retransmit_stop = None
            transaction.retransmit_thread = None

    def _start_separate_timer(self, transaction):
        """
        Start a thread to handle separate mode.

        :type transaction: Transaction
        :param transaction: the transaction that is in processing
        :rtype : the Timer object
        """
        t = threading.Timer(defines.ACK_TIMEOUT, self._send_ack, (transaction,))
        t.start()
        return t

    @staticmethod
    def _stop_separate_timer(timer):
        """
        Stop the separate Thread if an answer has been already provided to the client.

        :param timer: The Timer object
        """
        timer.cancel()

    def _send_ack(self, transaction):
        """
        Sends an ACK message for the request.

        :param transaction: the transaction that owns the request
        """

        ack = Message()
        ack.type = defines.Types['ACK']
        with transaction:
            if not transaction.request.acknowledged and transaction.request.type == defines.Types["CON"]:
                ack = self.messageLayer.send_empty(transaction, transaction.request, ack)
                if ack.type is not None and ack.mid is not None:
                    self.send_datagram(ack)

    def notify(self, resource):
        """
        Notifies the observers of a certain resource.

        :param resource: the resource
        """
        observers = self.observeLayer.notify(resource)
        logger.debug("Notify")
        for transaction in observers:
            with transaction:
                transaction.response = None
                transaction = self.requestLayer.receive_request(transaction)
                transaction = self.observeLayer.send_response(transaction)
                transaction = self.blockLayer.send_response(transaction)
                transaction = self.messageLayer.send_response(transaction)
                if transaction.response is not None:
                    if transaction.response.type == defines.Types["CON"]:
                        self._start_retransmission(transaction, transaction.response)

                    self.send_datagram(transaction.response)
