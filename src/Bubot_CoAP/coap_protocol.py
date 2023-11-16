import asyncio
import logging
from asyncio import Protocol
from typing import Optional

from Bubot_CoAP.messages.numbers import NON
from Bubot_CoAP.messages.option import Option
from . import defines
from .messages.message import Message
from .messages.request import Request
from .messages.response import Response
from .serializer_tcp import SerializerTcp

logger = logging.getLogger('Bubot_CoAP')


class RFC8323Remote:
    """Mixin for Remotes for all the common RFC8323 processing

    Implementations still need the per-transport parts, especially a
    _send_message and an _abort_with implementation.
    """

    # CSM received from the peer. The receive hook should abort suitably when
    # receiving a non-CSM message and this is not set yet.
    _remote_settings: Optional[Message]

    # Parameter usually set statically per implementation
    _my_max_message_size = 1024 * 1024

    def __init__(self):
        self._remote_settings = None

    is_multicast = False
    is_multicast_locally = False

    # implementing interfaces.EndpointAddress

    def __repr__(self):
        return "<%s at %#x, hostinfo %s, local %s>" % (
            type(self).__name__, id(self), self.hostinfo, self.hostinfo_local)

    @property
    def hostinfo(self):
        # keeping _remote_hostinfo and _local_hostinfo around structurally rather than in
        # hostinfo / hostinfo_local form looks odd now, but on the long run the
        # remote should be able to tell the message what its default Uri-Host
        # value is
        return util.hostportjoin(*self._remote_hostinfo)

    @property
    def hostinfo_local(self):
        return util.hostportjoin(*self._local_hostinfo)

    @property
    def uri_base(self):
        if self._local_is_server:
            raise error.AnonymousHost("Client side of %s can not be expressed as a URI" % self._ctx._scheme)
        else:
            return self._ctx._scheme + '://' + self.hostinfo

    @property
    def uri_base_local(self):
        if self._local_is_server:
            return self._ctx._scheme + '://' + self.hostinfo_local
        else:
            raise error.AnonymousHost("Client side of %s can not be expressed as a URI" % self._ctx._scheme)

    @property
    def maximum_block_size_exp(self):
        if self._remote_settings is None:
            # This is assuming that we can do BERT, so a first Block1 would be
            # exponent 7 but still only 1k -- because by the time we send this,
            # we typically haven't seen a CSM yet, so we'd be stuck with 6
            # because 7959 says we can't increase the exponent...
            #
            # FIXME: test whether we're properly using lower block sizes if
            # server says that szx=7 is not OK.
            return 7

        max_message_size = (self._remote_settings or {}).get('max-message-size', 1152)
        has_blockwise = (self._remote_settings or {}).get('block-wise-transfer', False)
        if max_message_size > 1152 and has_blockwise:
            return 7
        return 6  # FIXME: deal with smaller max-message-size

    @property
    def maximum_payload_size(self):
        # see maximum_payload_size of interfaces comment
        slack = 100

        max_message_size = (self._remote_settings or {}).get('max-message-size', 1152)
        has_blockwise = (self._remote_settings or {}).get('block-wise-transfer', False)
        if max_message_size > 1152 and has_blockwise:
            return ((max_message_size - 128) // 1024) * 1024 + slack
        return 1024 + slack  # FIXME: deal with smaller max-message-size

    @property
    def blockwise_key(self):
        return (self._remote_hostinfo, self._local_hostinfo)

    # Utility methods for implementing an RFC8323 transport

    def _send_initial_csm(self):
        my_csm = Message()
        # this is a tad awkward in construction because the options objects
        # were designed under the assumption that the option space is constant
        # for all message codes.
        my_csm.type = NON
        option = Option()
        option.number = defines.OptionRegistry.MAX_MESSAGE_SIZE.number
        option.value = defines.OptionRegistry.MAX_MESSAGE_SIZE.default
        my_csm.add_option(option)
        # block_length = optiontypes.UintOption(2, self._my_max_message_size)
        # my_csm.opt.add_option(block_length)
        # supports_block = optiontypes.UintOption(4, 0)
        # my_csm.opt.add_option(supports_block)
        self._send_message(my_csm)

    def _process_signaling(self, msg):
        if msg.code == CSM:
            if self._remote_settings is None:
                self._remote_settings = {}
            for opt in msg.opt.option_list():
                # FIXME: this relies on the relevant option numbers to be
                # opaque; message parsing should already use the appropriate
                # option types, or re-think the way options are parsed
                if opt.number == 2:
                    self._remote_settings['max-message-size'] = int.from_bytes(opt.value, 'big')
                elif opt.number == 4:
                    self._remote_settings['block-wise-transfer'] = True
                elif opt.number.is_critical():
                    self.abort("Option not supported", bad_csm_option=opt.number)
                else:
                    pass  # ignoring elective CSM options
        elif msg.code in (PING, PONG, RELEASE, ABORT):
            # not expecting data in any of them as long as Custody is not implemented
            for opt in msg.opt.option_list():
                if opt.number.is_critical():
                    self.abort("Unknown critical option")
                else:
                    pass

            if msg.code == PING:
                pong = Message(code=PONG, token=msg.token)
                self._send_message(pong)
            elif msg.code == PONG:
                pass
            elif msg.code == RELEASE:
                # The behavior SHOULD be enhanced to answer outstanding
                # requests, but it is unclear to which extent this side may
                # still use the connection.
                self.log.info("Received Release, closing on this end (options: %s)", msg.opt)
                raise CloseConnection(error.RemoteServerShutdown("Peer released connection"))
            elif msg.code == ABORT:
                self.log.warning("Received Abort (options: %s)", msg.opt)
                raise CloseConnection(error.RemoteServerShutdown("Peer aborted connection"))
        else:
            self.abort("Unknown signalling code")

    def abort(self, errormessage=None, bad_csm_option=None):
        self.log.warning("Aborting connection: %s", errormessage)
        abort_msg = Message(code=ABORT)
        if errormessage is not None:
            abort_msg.payload = errormessage.encode('utf8')
        if bad_csm_option is not None:
            bad_csm_option_option = optiontypes.UintOption(2, bad_csm_option)
            abort_msg.opt.add_option(bad_csm_option_option)
        self._abort_with(abort_msg)

    async def release(self):
        """Send Release message, (not implemented:) wait for connection to be
        actually closed by the peer.

        Subclasses should extend this to await closing of the connection,
        especially if they'd get into lock-up states otherwise (was would
        WebSockets).
        """
        self.log.info("Releasing connection %s", self)
        release_msg = Message(code=RELEASE)
        self._send_message(release_msg)

        try:
            # FIXME: we could wait for the peer to close the connection, but a)
            # that'll need some work on the interface between this module and
            # ws/tcp, and b) we have no peers to test this with that would
            # produce any sensible data (as aiocoap on release just closes).
            pass
        except asyncio.CancelledError:
            self.log.warning(
                "Connection %s was not closed by peer in time after release",
                self
            )


class CoapProtocol(Protocol, RFC8323Remote):
    def __init__(self, server, endpoint, *, is_server=False, **kwargs):
        super(RFC8323Remote, self).__init__()
        self.server = server
        self.transport = None
        self.endpoint = endpoint
        self.is_server = is_server
        self._local_host_info = None
        self._remote_host_info = None
        self._spool = b""

    @property
    def scheme(self):
        return self._ctx._scheme

    def _send_message(self, message: Message):
        # self.log.debug("Sending message: %r", message)
        serializer = SerializerTcp()
        raw_message = serializer.serialize(message)

        self.transport.write(bytes(raw_message))

    def _abort_with(self, abort_msg):
        if self.transport is not None:
            self._send_message(abort_msg)
            self.transport.close()
        else:
            # FIXME: find out how this happens; i've only seen it after nmap
            # runs against an aiocoap server and then shutting it down.
            # "poisoning" the object to make sure this can not be exploited to
            # bypass the server shutdown.
            self._ctx = None

    def connection_made(self, transport):
        logger.debug(f'connection_made')
        self.transport = transport

        ssl_object = transport.get_extra_info('ssl_object')
        if ssl_object is not None:
            server_name = getattr(ssl_object, "indicated_server_name", None)
        else:
            server_name = None

        # `host` already contains the interface identifier, so throwing away
        # scope and interface identifier
        self._local_host_info = transport.get_extra_info('sockname')[:2]
        self._remote_host_info = transport.get_extra_info('peername')[:2]

        # def none_default_port(sockname):
        #     return (sockname[0], None if sockname[1] == self._ctx._default_port else sockname[1])
        #
        # self._local_hostinfo = none_default_port(self._local_hostinfo)
        # self._remote_hostinfo = none_default_port(self._remote_hostinfo)

        # # SNI information available
        # if server_name is not None:
        #     if self._local_is_server:
        #         self._local_hostinfo = (server_name, self._local_hostinfo[1])
        #     else:
        #         self._remote_hostinfo = (server_name, self._remote_hostinfo[1])

        if self.is_server:
            self._send_initial_csm()

    def _send_initial_csm(self):
        my_csm = Message()
        # this is a tad awkward in construction because the options objects
        # were designed under the assumption that the option space is constant
        # for all message codes.
        my_csm.code = defines.Codes.CSM.number
        option = Option()
        option.number = defines.OptionRegistry.MAX_MESSAGE_SIZE.number
        option.value = defines.OptionRegistry.MAX_MESSAGE_SIZE.default
        my_csm.add_option(option)
        # block_length = optiontypes.UintOption(2, self._my_max_message_size)
        # my_csm.opt.add_option(block_length)
        # supports_block = optiontypes.UintOption(4, 0)
        # my_csm.opt.add_option(supports_block)
        self._send_message(my_csm)

    def data_received(self, data):
        try:
            ...
            # A rope would be more efficient here, but the expected case is that
            # _spool is b"" and spool gets emptied soon -- most messages will just
            # fit in a single TCP package and not be nagled together.
            #
            # (If this does become a bottleneck, say self._spool = SomeRope(b"")
            # and barely change anything else).

            self._spool += data

            while True:
                msg_header = _extract_message_size(self._spool)
                if msg_header is None:
                    break
                msg_size = sum(msg_header)
                if msg_size > self._my_max_message_size:
                    self.abort("Overly large message announced")
                    return

                if msg_size > len(self._spool):
                    break

                data = self._spool[:msg_size]

                serializer = SerializerTcp()
                message = serializer.deserialize(data, self._remote_host_info)

                if isinstance(message, int):  # todo переделать в try catch
                    # if data[0] == b'\x16':  # client hello
                    return self.datagram_received_bad_message(message, self._remote_host_info)

                message.destination = self._local_host_info
                message.multicast = False
                if self.is_server:
                    message.scheme = self.endpoint.scheme
                    message.family = self.endpoint.family

                logger.debug("receive_datagram - " + str(message))
                if isinstance(message, Request):
                    self.server.loop.create_task(self.datagram_received_request(message))
                elif isinstance(message, Response):
                    self.server.loop.create_task(self.datagram_received_response(message))
                else:  # is Message
                    self.server.loop.create_task(self.datagram_received_message(message))
            #
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

    def connection_lost(self, exc):
        logger.debug(f'Connection closed {exc}')

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


def _extract_message_size(data: bytes):
    """Read out the full length of a CoAP messsage represented by data.

    Returns None if data is too short to read the (full) length.

    The number returned is the number of bytes that has to be read into data to
    start reading the next message; it consists of a constant term, the token
    length and the extended length of options-plus-payload."""

    if not data:
        return None

    l = data[0] >> 4
    tokenoffset = 2
    tkl = data[0] & 0x0f

    if l >= 13:
        if l == 13:
            extlen = 1
            offset = 13
        elif l == 14:
            extlen = 2
            offset = 269
        else:
            extlen = 4
            offset = 65805
        if len(data) < extlen + 1:
            return None
        tokenoffset = 2 + extlen
        l = int.from_bytes(data[1:1 + extlen], "big") + offset
    return tokenoffset, tkl, l


def _decode_message(data: bytes) -> Message:
    tokenoffset, tkl, _ = _extract_message_size(data)
    if tkl > 8:
        raise error.UnparsableMessage("Overly long token")
    code = data[tokenoffset - 1]
    token = data[tokenoffset:tokenoffset + tkl]

    msg = Message(code=code, token=token)

    msg.payload = msg.opt.decode(data[tokenoffset + tkl:])

    return msg


def _encode_length(l: int):
    if l < 13:
        return (l, b"")
    elif l < 269:
        return (13, (l - 13).to_bytes(1, 'big'))
    elif l < 65805:
        return (14, (l - 269).to_bytes(2, 'big'))
    else:
        return (15, (l - 65805).to_bytes(4, 'big'))


def _serialize(msg: Message) -> bytes:
    data = [msg.opt.encode()]
    if msg.payload:
        data += [b'\xff', msg.payload]
    data = b"".join(data)
    l, extlen = _encode_length(len(data))

    tkl = len(msg.token)
    if tkl > 8:
        raise ValueError("Overly long token")

    return b"".join((
        bytes(((l << 4) | tkl,)),
        extlen,
        bytes((msg.code,)),
        msg.token,
        data
    ))
