import ctypes
import logging
import struct

import cbor2

from . import defines
from .messages.message import Message
from .messages.option import Option
from .messages.request import Request
from .messages.response import Response
from .serializer import Serializer

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


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


class SerializerTcp(Serializer):
    """
    Serializer class to serialize and deserialize CoAP message to/from udp streams.
    """

    @staticmethod
    def deserialize(datagram, source):
        """
        De-serialize a stream of byte to a message.

        :param datagram: the incoming udp message
        :param source: the source address and port (ip, port)
        :return: the message
        :rtype: Message
        """
        try:
            tokenoffset, tkl, _ = _extract_message_size(datagram)
            if tkl > 8:
                raise UnicodeDecodeError("Overly long token")
            code = datagram[tokenoffset - 1]
            token = datagram[tokenoffset:tokenoffset + tkl]

            # fmt = "!BBH"
            # pos = struct.calcsize(fmt)
            # s = struct.Struct(fmt)
            # values = s.unpack_from(datagram)
            # first = values[0]
            # code = values[1]
            # mid = values[2]
            # version = (first & 0xC0) >> 6
            # message_type = (first & 0x30) >> 4
            # token_length = (first & 0x0F)
            if Serializer.is_response(code):
                message = Response()
                message.code = code
            elif Serializer.is_request(code):
                message = Request()
                message.code = code
            else:
                message = Message()
                message.code = code
            message.source = source
            message.destination = None
            # message.version = version
            # message.type = message_type
            # message.mid = mid
            # if token_length > 0:
            #     message.token = datagram[pos:pos + token_length]
            # else:
            #     message.token = None
            message.token = token

            current_option = 0
            values = datagram[tokenoffset + tkl:]
            length_packet = len(values)
            pos = 0
            while pos < length_packet:
                next_byte = struct.unpack("B", values[pos].to_bytes(1, "big"))[0]
                pos += 1
                if next_byte != int(defines.PAYLOAD_MARKER):
                    # the first 4 bits of the byte represent the option delta
                    # delta = self._reader.read(4).uint
                    num, option_length, pos = Serializer.read_option_value_len_from_byte(next_byte, pos, values)
                    # logger.debug("option value (delta): %d len: %d", num, option_length)
                    current_option += num
                    # read option
                    try:
                        option_item = defines.OptionRegistry.LIST[current_option]
                    except KeyError:
                        (opt_critical, _, _) = defines.OptionRegistry.get_option_flags(current_option)
                        if opt_critical:
                            raise AttributeError("Critical option %s unknown" % current_option)
                        else:
                            # If the non-critical option is unknown
                            # (vendor-specific, proprietary) - just skip it
                            logger.warning("unrecognized option %d", current_option)
                    else:
                        if option_length == 0:
                            value = None
                        elif option_item.value_type == defines.INTEGER:
                            tmp = values[pos: pos + option_length]
                            value = 0
                            for b in tmp:
                                value = (value << 8) | struct.unpack("B", b.to_bytes(1, "big"))[0]
                        elif option_item.value_type == defines.OPAQUE:
                            tmp = values[pos: pos + option_length]
                            value = tmp
                        else:
                            value = values[pos: pos + option_length]

                        option = Option()
                        option.number = current_option
                        option.value = Serializer.convert_to_raw(current_option, value, option_length)

                        message.add_option(option)
                        if option.number == defines.OptionRegistry.CONTENT_TYPE.number:
                            message.payload_type = option.value
                    finally:
                        pos += option_length
                else:

                    if length_packet <= pos:
                        # log.err("Payload Marker with no payload")
                        raise AttributeError("Packet length %s, pos %s" % (length_packet, pos))
                    message.payload = ""
                    payload = values[pos:]
                    message.payload = payload

                    pos += len(payload)

            return message
        except AttributeError:
            return defines.Codes.BAD_REQUEST.number
        except struct.error:
            return defines.Codes.BAD_REQUEST.number
        except UnicodeDecodeError as e:
            logger.debug(e)
            return defines.Codes.BAD_REQUEST.number

    @staticmethod
    def serialize(message):
        """
        Serialize a message to a udp packet

        :type message: Message
        :param message: the message to be serialized
        :rtype: stream of byte
        :return: the message serialized
        """
        fmt = "!BBH"
        fmt = ""
        # if message.token is None:
        #     tkl = 0
        # else:
        #     tkl = len(message.token)
        # tmp = (defines.VERSION << 2)
        # tmp |= message.type
        # tmp <<= 4
        # tmp |= tkl
        #
        # values = [tmp, message.code, message.mid]
        values = []

        # if message.token is not None and tkl > 0:
        #     fmt += "%ss" % tkl
        #     values.append(message.token)

        options = Serializer.as_sorted_list(message.options)  # already sorted
        lastoptionnumber = 0
        for option in options:

            # write 4-bit option delta
            optiondelta = option.number - lastoptionnumber
            optiondeltanibble = Serializer.get_option_nibble(optiondelta)
            tmp = (optiondeltanibble << defines.OPTION_DELTA_BITS)

            # write 4-bit option length
            optionlength = option.length
            optionlengthnibble = Serializer.get_option_nibble(optionlength)
            tmp |= optionlengthnibble
            fmt += "B"
            values.append(tmp)

            # write extended option delta field (0 - 2 bytes)
            if optiondeltanibble == 13:
                fmt += "B"
                values.append(optiondelta - 13)
            elif optiondeltanibble == 14:
                fmt += "H"
                values.append(optiondelta - 269)

            # write extended option length field (0 - 2 bytes)
            if optionlengthnibble == 13:
                fmt += "B"
                values.append(optionlength - 13)
            elif optionlengthnibble == 14:
                fmt += "H"
                values.append(optionlength - 269)

            # write option value
            if optionlength > 0:
                opt_type = defines.OptionRegistry.LIST[option.number].value_type
                if opt_type == defines.INTEGER:
                    words = Serializer.int_to_words(option.value, optionlength, 8)
                    for num in range(0, optionlength):
                        fmt += "B"
                        values.append(words[num])
                elif opt_type == defines.STRING:
                    fmt += str(len(bytes(option.value, "utf-8"))) + "s"
                    values.append(bytes(option.value, "utf-8"))
                else:  # OPAQUE
                    for b in option.value:
                        fmt += "B"
                        values.append(b)

            # update last option number
            lastoptionnumber = option.number

        payload = message.payload

        if payload is not None and len(payload) > 0:
            # if payload is present and of non-zero length, it is prefixed by
            # an one-byte Payload Marker (0xFF) which indicates the end of
            # options and the start of the payload

            fmt += "B"
            values.append(defines.PAYLOAD_MARKER)

            if isinstance(payload, bytes):
                fmt += str(len(payload)) + "s"
                values.append(payload)

            else:
                # raise ValueError('Not bytes payload')
                # try:
                #     _encoder = encoder[message.content_type]
                # except KeyError:
                #     _encoder =
                _data = string_encode(payload)
                fmt += str(len(_data)) + "s"
                values.append(_data)

        datagram = None
        # if values[1] is None:
        #     values[1] = 0
        # if values[2] is None:
        #     values[2] = 0
        try:
            s = struct.Struct(fmt)
            datagram = ctypes.create_string_buffer(s.size)
            s.pack_into(datagram, 0, *values)
        except struct.error:
            # The .exception method will report on the exception encountered
            # and provide a traceback.
            logger.debug(fmt)
            logger.debug(values)
            logging.exception('Failed to pack structure')

        l, extlen = _encode_length(len(datagram))
        token = message.token if message.token else b''
        tkl = len(token)
        if tkl > 8:
            raise ValueError("Overly long token")
        datagram = b"".join((
            bytes(((l << 4) | tkl,)),
            extlen,
            bytes((message.code,)),
            token,
            datagram
            ))
        return datagram

    @staticmethod
    def is_request(code):
        """
        Checks if is request.

        :return: True, if is request
        """
        return defines.REQUEST_CODE_LOWER_BOUND <= code <= defines.REQUEST_CODE_UPPER_BOUND

    @staticmethod
    def is_response(code):
        """
        Checks if is response.

        :return: True, if is response
        """
        return defines.RESPONSE_CODE_LOWER_BOUND <= code <= defines.RESPONSE_CODE_UPPER_BOUND

    @staticmethod
    def read_option_value_len_from_byte(byte, pos, values):
        """
        Calculates the value and length used in the extended option fields.

        :param byte: 1-byte option header value.
        :return: the value and length, calculated from the header including the extended fields.
        """
        h_nibble = (byte & 0xF0) >> 4
        l_nibble = byte & 0x0F
        value = 0
        length = 0
        if h_nibble <= 12:
            value = h_nibble
        elif h_nibble == 13:
            value = struct.unpack("!B", values[pos].to_bytes(1, "big"))[0] + 13
            pos += 1
        elif h_nibble == 14:
            s = struct.Struct("!H")
            value = s.unpack_from(values[pos:pos + 2])[0] + 269
            pos += 2
        else:
            raise AttributeError("Unsupported option number nibble " + str(h_nibble))

        if l_nibble <= 12:
            length = l_nibble
        elif l_nibble == 13:
            length = struct.unpack("!B", values[pos].to_bytes(1, "big"))[0] + 13
            pos += 1
        elif l_nibble == 14:
            s = struct.Struct("!H")
            length = s.unpack_from(values[pos:pos + 2])[0] + 269
            pos += 2
        else:
            raise AttributeError("Unsupported option length nibble " + str(l_nibble))
        return value, length, pos

    @staticmethod
    def convert_to_raw(number, value, length):
        """
        Get the value of an option as bytes.

        :param number: the option number
        :param value: the option value
        :param length: the option length
        :return: the value of an option as a BitArray
        """

        opt_type = defines.OptionRegistry.LIST[number].value_type

        if length == 0 and opt_type != defines.INTEGER:
            return bytes()
        elif length == 0 and opt_type == defines.INTEGER:
            return 0
        elif opt_type == defines.STRING:
            if isinstance(value, bytes):
                return value.decode("utf-8")
        elif opt_type == defines.OPAQUE:
            if isinstance(value, bytes):
                return value
            else:
                return bytes(value, "utf-8")
        if isinstance(value, tuple):
            value = value[0]
        if isinstance(value, str):
            value = str(value)
        if isinstance(value, str):
            return bytes(value, "utf-8")
        elif isinstance(value, int):
            return value
        else:
            return bytes(value)

    @staticmethod
    def as_sorted_list(options):
        """
        Returns all options in a list sorted according to their option numbers.

        :return: the sorted list
        """
        if len(options) > 0:
            options = sorted(options, key=lambda o: o.number)
        return options

    @staticmethod
    def get_option_nibble(optionvalue):
        """
        Returns the 4-bit option header value.

        :param optionvalue: the option value (delta or length) to be encoded.
        :return: the 4-bit option header value.
         """
        if optionvalue <= 12:
            return optionvalue
        elif optionvalue <= 255 + 13:
            return 13
        elif optionvalue <= 65535 + 269:
            return 14
        else:
            raise AttributeError("Unsupported option delta " + optionvalue)

    @staticmethod
    def int_to_words(int_val, num_words=4, word_size=32):
        """
        Convert a int value to bytes.

        :param int_val: an arbitrary length Python integer to be split up.
            Network byte order is assumed. Raises an IndexError if width of
            integer (in bits) exceeds word_size * num_words.

        :param num_words: number of words expected in return value tuple.

        :param word_size: size/width of individual words (in bits).

        :return: a list of fixed width words based on provided parameters.
        """
        max_int = 2 ** (word_size * num_words) - 1
        max_word_size = 2 ** word_size - 1

        if not 0 <= int_val <= max_int:
            raise AttributeError('integer %r is out of bounds!' % hex(int_val))

        words = []
        for _ in range(num_words):
            word = int_val & max_word_size
            words.append(int(word))
            int_val >>= word_size
        words.reverse()

        return words

    def diffie_hellman_key_exchange(self):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import dh
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        # Generate some parameters. These can be reused.
        parameters = dh.generate_parameters(generator=2, key_size=2048)
        # Generate a private key for use in the exchange.
        server_private_key = parameters.generate_private_key()
        # In a real handshake the peer is a remote client. For this
        # example we'll generate another local private key though. Note that in
        # a DH handshake both peers must agree on a common set of parameters.
        peer_private_key = parameters.generate_private_key()
        shared_key = server_private_key.exchange(peer_private_key.public_key())
        # Perform key derivation.
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)
        # And now we can demonstrate that the handshake performed in the
        # opposite direction gives the same final value
        same_shared_key = peer_private_key.exchange(
            server_private_key.public_key()
        )
        same_derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(same_shared_key)
        derived_key == same_derived_key


def cbor_loads(payload):
    return cbor2.loads(payload)


def cbor_dumps(payload):
    return cbor2.dumps(payload) if payload else b''


def string_encode(payload):
    try:
        return bytes(payload, "utf-8")
    except Exception as err:
        raise err


def string_decode(payload):
    return cbor2.loads(payload)


encoder = {
    10000: cbor_dumps
}
decoder = {
    10000: cbor_loads
}
