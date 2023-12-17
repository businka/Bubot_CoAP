import logging
from asyncio import Protocol

from Bubot_CoAP.messages.option import Option
from . import defines
from . import utils
from .coap_protocol import CoapProtocol
from .messages.message import Message
from .serializer_tcp import SerializerTcp

logger = logging.getLogger('Bubot_CoAP')


# class RFC8323Remote:
#     """Mixin for Remotes for all the common RFC8323 processing
#
#     Implementations still need the per-transport parts, especially a
#     send_message and an _abort_with implementation.
#     """
#
#     # CSM received from the peer. The receive hook should abort suitably when
#     # receiving a non-CSM message and this is not set yet.
#     _remote_settings: Optional[Message]
#
#     # Parameter usually set statically per implementation
#     _my_max_message_size = 1024 * 1024
#
#     def __init__(self):
#         self._remote_settings = None
#
#     is_multicast = False
#     is_multicast_locally = False
#
#     # implementing interfaces.EndpointAddress
#
#     def __repr__(self):
#         return "<%s at %#x, hostinfo %s, local %s>" % (
#             type(self).__name__, id(self), self.hostinfo, self.hostinfo_local)
#
#     @property
#     def hostinfo(self):
#         # keeping _remote_hostinfo and _local_hostinfo around structurally rather than in
#         # hostinfo / hostinfo_local form looks odd now, but on the long run the
#         # remote should be able to tell the message what its default Uri-Host
#         # value is
#         return util.hostportjoin(*self._remote_hostinfo)
#
#     @property
#     def hostinfo_local(self):
#         return util.hostportjoin(*self._local_hostinfo)
#
#     @property
#     def uri_base(self):
#         if self._local_is_server:
#             raise error.AnonymousHost("Client side of %s can not be expressed as a URI" % self._ctx._scheme)
#         else:
#             return self._ctx._scheme + '://' + self.hostinfo
#
#     @property
#     def uri_base_local(self):
#         if self._local_is_server:
#             return self._ctx._scheme + '://' + self.hostinfo_local
#         else:
#             raise error.AnonymousHost("Client side of %s can not be expressed as a URI" % self._ctx._scheme)
#
#     @property
#     def maximum_block_size_exp(self):
#         if self._remote_settings is None:
#             # This is assuming that we can do BERT, so a first Block1 would be
#             # exponent 7 but still only 1k -- because by the time we send this,
#             # we typically haven't seen a CSM yet, so we'd be stuck with 6
#             # because 7959 says we can't increase the exponent...
#             #
#             # FIXME: test whether we're properly using lower block sizes if
#             # server says that szx=7 is not OK.
#             return 7
#
#         max_message_size = (self._remote_settings or {}).get('max-message-size', 1152)
#         has_blockwise = (self._remote_settings or {}).get('block-wise-transfer', False)
#         if max_message_size > 1152 and has_blockwise:
#             return 7
#         return 6  # FIXME: deal with smaller max-message-size
#
#     @property
#     def maximum_payload_size(self):
#         # see maximum_payload_size of interfaces comment
#         slack = 100
#
#         max_message_size = (self._remote_settings or {}).get('max-message-size', 1152)
#         has_blockwise = (self._remote_settings or {}).get('block-wise-transfer', False)
#         if max_message_size > 1152 and has_blockwise:
#             return ((max_message_size - 128) // 1024) * 1024 + slack
#         return 1024 + slack  # FIXME: deal with smaller max-message-size
#
#     @property
#     def blockwise_key(self):
#         return (self._remote_hostinfo, self._local_hostinfo)
#
#     # Utility methods for implementing an RFC8323 transport
#
#     def _send_initial_csm(self):
#         my_csm = Message()
#         # this is a tad awkward in construction because the options objects
#         # were designed under the assumption that the option space is constant
#         # for all message codes.
#         my_csm.type = NON
#         option = Option()
#         option.number = defines.OptionRegistry.MAX_MESSAGE_SIZE.number
#         option.value = defines.OptionRegistry.MAX_MESSAGE_SIZE.default
#         my_csm.add_option(option)
#         # block_length = optiontypes.UintOption(2, self._my_max_message_size)
#         # my_csm.opt.add_option(block_length)
#         # supports_block = optiontypes.UintOption(4, 0)
#         # my_csm.opt.add_option(supports_block)
#         self.send_message(my_csm)
#
#     def _process_signaling(self, msg):
#         if msg.code == CSM:
#             if self._remote_settings is None:
#                 self._remote_settings = {}
#             for opt in msg.opt.option_list():
#                 # FIXME: this relies on the relevant option numbers to be
#                 # opaque; message parsing should already use the appropriate
#                 # option types, or re-think the way options are parsed
#                 if opt.number == 2:
#                     self._remote_settings['max-message-size'] = int.from_bytes(opt.value, 'big')
#                 elif opt.number == 4:
#                     self._remote_settings['block-wise-transfer'] = True
#                 elif opt.number.is_critical():
#                     self.abort("Option not supported", bad_csm_option=opt.number)
#                 else:
#                     pass  # ignoring elective CSM options
#         elif msg.code in (PING, PONG, RELEASE, ABORT):
#             # not expecting data in any of them as long as Custody is not implemented
#             for opt in msg.opt.option_list():
#                 if opt.number.is_critical():
#                     self.abort("Unknown critical option")
#                 else:
#                     pass
#
#             if msg.code == PING:
#                 pong = Message(code=PONG, token=msg.token)
#                 self.send_message(pong)
#             elif msg.code == PONG:
#                 pass
#             elif msg.code == RELEASE:
#                 # The behavior SHOULD be enhanced to answer outstanding
#                 # requests, but it is unclear to which extent this side may
#                 # still use the connection.
#                 self.log.info("Received Release, closing on this end (options: %s)", msg.opt)
#                 raise CloseConnection(error.RemoteServerShutdown("Peer released connection"))
#             elif msg.code == ABORT:
#                 self.log.warning("Received Abort (options: %s)", msg.opt)
#                 raise CloseConnection(error.RemoteServerShutdown("Peer aborted connection"))
#         else:
#             self.abort("Unknown signalling code")
#
#     def abort(self, errormessage=None, bad_csm_option=None):
#         self.log.warning("Aborting connection: %s", errormessage)
#         abort_msg = Message(code=ABORT)
#         if errormessage is not None:
#             abort_msg.payload = errormessage.encode('utf8')
#         if bad_csm_option is not None:
#             bad_csm_option_option = optiontypes.UintOption(2, bad_csm_option)
#             abort_msg.opt.add_option(bad_csm_option_option)
#         self._abort_with(abort_msg)
#
#     async def release(self):
#         """Send Release message, (not implemented:) wait for connection to be
#         actually closed by the peer.
#
#         Subclasses should extend this to await closing of the connection,
#         especially if they'd get into lock-up states otherwise (was would
#         WebSockets).
#         """
#         self.log.info("Releasing connection %s", self)
#         release_msg = Message(code=RELEASE)
#         self.send_message(release_msg)
#
#         try:
#             # FIXME: we could wait for the peer to close the connection, but a)
#             # that'll need some work on the interface between this module and
#             # ws/tcp, and b) we have no peers to test this with that would
#             # produce any sensible data (as aiocoap on release just closes).
#             pass
#         except asyncio.CancelledError:
#             self.log.warning(
#                 "Connection %s was not closed by peer in time after release",
#                 self
#             )


class CoapTcpProtocol(CoapProtocol, Protocol):
    def __init__(self, server, endpoint, *, is_server=False, **kwargs):
        super(CoapTcpProtocol, self).__init__(server, endpoint)
        self._transport = None
        self.is_server = is_server
        self.remote_address = None
        self._spool = b""
        self.id = None
        if not is_server:
            self.endpoint.protocol = self

    # @property
    # def scheme(self):
    #     return self._ctx._scheme

    # def send_message(self, message: Message):
    #     # self.log.debug("Sending message: %r", message)
    #     serializer = SerializerTcp()
    #     raw_message = serializer.serialize(message)
    #     self._transport.write(bytes(raw_message))

    def send(self, data):
        logger.debug(f"Send TCP {len(data)} bytes From {self.endpoint.address[0]}: {self.endpoint.address[1]} "
                     f"To {self.remote_address[0]}:{self.remote_address[1]}")
        self._transport.write(bytes(data))

    # def _abort_with(self, abort_msg):
    #     if self._transport is not None:
    #         self.send_message(abort_msg)
    #         self._transport.close()
    #     else:
    #         # FIXME: find out how this happens; i've only seen it after nmap
    #         # runs against an aiocoap server and then shutting it down.
    #         # "poisoning" the object to make sure this can not be exploited to
    #         # bypass the server shutdown.
    #         self._ctx = None

    def connection_made(self, transport):
        self.endpoint.address = transport.get_extra_info('sockname')[:2]
        self.remote_address = transport.get_extra_info('peername')[:2]
        self.id = utils.str_append_hash(self.remote_address[0], self.remote_address[1])
        self.endpoint.pool[self.id] = self

        if self.is_server:
            logger.info(f"Server made TCP connection to {self.endpoint.address[0]}: "
                        f"{self.endpoint.address[1]} from {self.remote_address[0]}: {self.remote_address[1]}")
        else:
            logger.info(f"Client made TCP connection to {self.remote_address[0]}: "
                        f"{self.remote_address[1]} from {self.endpoint.address[0]}: {self.endpoint.address[1]}")
        self._transport = transport

        ssl_object = transport.get_extra_info('ssl_object')
        if ssl_object is not None:
            server_name = getattr(ssl_object, "indicated_server_name", None)
        else:
            server_name = None

        # `host` already contains the interface identifier, so throwing away
        # scope and interface identifier

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
        if self.server.client_manager:
            self.server.loop.create_task(self.server.client_manager.connection_made(self))

    def connection_lost(self, exc):
        if self.is_server:
            logger.info(f"Server close TCP connection to {self.endpoint.address[0]}: "
                        f"{self.endpoint.address[1]} from {self.remote_address[0]}: {self.remote_address[1]}")
        else:
            logger.info(f"Client close TCP connection to {self.remote_address[0]}: "
                        f"{self.remote_address[1]} from {self.endpoint.address[0]}: {self.endpoint.address[1]}")
        try:
            if self.server.client_manager:
                self.server.loop.create_task(self.server.client_manager.connection_lost(self, exc))
        finally:
            self.endpoint.pool.pop(self.id, None)

    def _send_initial_csm(self):
        message = Message()
        # this is a tad awkward in construction because the options objects
        # were designed under the assumption that the option space is constant
        # for all message codes.
        message.code = defines.Codes.CSM.number
        message.add_option(
            Option(defines.OptionRegistry.MAX_MESSAGE_SIZE, defines.OptionRegistry.MAX_MESSAGE_SIZE.default))
        # block_length = optiontypes.UintOption(2, self._my_max_message_size)
        # my_csm.opt.add_option(block_length)
        # supports_block = optiontypes.UintOption(4, 0)
        # my_csm.opt.add_option(supports_block)
        message.destination = self.remote_address
        message.source = self.endpoint.address
        serializer = SerializerTcp()
        raw_message = serializer.serialize(message)
        self.send(raw_message)
        # self.endpoint.send_message(message)

    def data_received(self, data):
        try:
            ...
            # A rope would be more efficient here, but the expected case is that
            # _spool is b"" and spool gets emptied soon -- most messages will just
            # fit in a single TCP package and not be nagled together.
            #
            # (If this does become a bottleneck, say self._spool = SomeRope(b"")
            # and barely change anything else).
            logger.debug(f"Recv TCP {len(data)} bytes From {self.remote_address[0]}: {self.remote_address[1]} "
                         f"To  {self.endpoint.address[0]}: {self.endpoint.address[1]} ")
            self._spool += data

            while True:
                msg_header = _extract_message_size(self._spool)
                if msg_header is None:
                    break
                msg_size = sum(msg_header)
                # if msg_size > self._my_max_message_size:
                #     self.abort("Overly large message announced") TODO
                #     return

                if msg_size > len(self._spool):
                    break

                data = self._spool[:msg_size]

                serializer = SerializerTcp()
                message = serializer.deserialize(data, self.remote_address)
                # msg.remote = self

                self._spool = self._spool[msg_size:]

                if isinstance(message, int):  # todo переделать в try catch
                    # if data[0] == b'\x16':  # client hello
                    return self.datagram_received_bad_message(message, self.remote_address)

                message.destination = self.endpoint.address
                message.multicast = False
                # message.endpoint = self.endpoint
                if self.is_server:
                    message.scheme = self.endpoint.scheme
                    message.family = self.endpoint.family
                self.message_received(message)
                return
        except RuntimeError:
            logger.exception("Exception with Executor")

    async def update_res(self, href, data, **kwargs):
        ...

    def close(self):
        if self._transport:
            self._transport.close()


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


def _encode_length(l: int):
    if l < 13:
        return (l, b"")
    elif l < 269:
        return (13, (l - 13).to_bytes(1, 'big'))
    elif l < 65805:
        return (14, (l - 269).to_bytes(2, 'big'))
    else:
        return (15, (l - 65805).to_bytes(4, 'big'))
