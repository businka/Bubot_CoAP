# -*- coding: utf-8 -*-

import collections
import struct
from enum import Enum


class RequestClassCode(Enum):
    Method = 0
    Success = 2
    ClientError = 4
    ServerError = 5
    SignalingCodes = 7


class RequestSuccessCode(Enum):
    Created = 1
    Deleted = 2
    Valid = 3
    Changed = 4
    Content = 5
    Continue = 31


# class RequestServerErrorCode(Enum):
#     Bad Request
#     Unauthorized
#     Bad Option
#     Forbidden
#     Not Found
#     Method Not Allowed
#     Not Acceptable
#     Request Entity Incomplete
#     Conflict
#     Precondition Failed
#     Request Entity Too Large
#     Unsupported Content-Format
#
# class RequestClientErrorCode(Enum):

""" CoAP Parameters """

ACK_TIMEOUT = 2  # standard 2

SEPARATE_TIMEOUT = ACK_TIMEOUT / 2

MULTICAST_TIMEOUT = 35

ACK_RANDOM_FACTOR = 1.5

MAX_RETRANSMIT = 4

MAX_TRANSMIT_SPAN = ACK_TIMEOUT * (pow(2, (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR

MAX_LATENCY = 120  # 2 minutes

PROCESSING_DELAY = ACK_TIMEOUT

MAX_RTT = (2 * MAX_LATENCY) + PROCESSING_DELAY

EXCHANGE_LIFETIME = MAX_TRANSMIT_SPAN + (2 * MAX_LATENCY) + PROCESSING_DELAY

DISCOVERY_URL = "/.well-known/core"

ALL_COAP_NODES = "224.0.1.187"

ALL_COAP_NODES_IPV6 = "FF00::FD"

MAX_PAYLOAD = 1024

MAX_NON_NOTIFICATIONS = 10

BLOCKWISE_SIZE = 1024

"""  Message Format """

# number of bits used for the encoding of the CoAP version field.
VERSION_BITS = 2

# number of bits used for the encoding of the message type field.
TYPE_BITS = 2

# number of bits used for the encoding of the token length field.
TOKEN_LENGTH_BITS = 4

# number of bits used for the encoding of the request method/response code field.
CODE_BITS = 8

# number of bits used for the encoding of the message ID.
MESSAGE_ID_BITS = 16

# number of bits used for the encoding of the option delta field.
OPTION_DELTA_BITS = 4

# number of bits used for the encoding of the option delta field.
OPTION_LENGTH_BITS = 4

# One byte which indicates indicates the end of options and the start of the payload.
PAYLOAD_MARKER = 0xFF

# CoAP version supported by this Californium version.
VERSION = 1

# The lowest value of a request code.
REQUEST_CODE_LOWER_BOUND = 1

# The highest value of a request code.
REQUEST_CODE_UPPER_BOUND = 31

# The lowest value of a response code.
RESPONSE_CODE_LOWER_BOUND = 64

# The highest value of a response code.
RESPONSE_CODE_UPPER_BOUND = 191

corelinkformat = {
    'ct': 'content_type',
    'rt': 'resource_type',
    'if': 'interface_type',
    'sz': 'maximum_size_estimated',
    'obs': 'observing'
}

# The integer.
INTEGER = 0
# The string.
STRING = 1
# The opaque.
OPAQUE = 2
# The unknown.
UNKNOWN = 3

# Cache modes
FORWARD_PROXY = 0
REVERSE_PROXY = 1

OptionItem = collections.namedtuple('OptionItem', 'number name value_type repeatable default')


class OptionRegistry(object):
    """
    All CoAP options. Every option is represented as: (NUMBER, NAME, VALUE_TYPE, REPEATABLE, DEFAULT)
    """

    def __init__(self):
        pass

    RESERVED = OptionItem(0, "Reserved", UNKNOWN, True, None)
    IF_MATCH = OptionItem(1, "If-Match", OPAQUE, True, None)
    URI_HOST = OptionItem(3, "Uri-Host", STRING, True, None)
    ETAG = OptionItem(4, "ETag", OPAQUE, True, None)
    IF_NONE_MATCH = OptionItem(5, "If-None-Match", OPAQUE, False, None)
    OBSERVE = OptionItem(6, "Observe", INTEGER, False, 0)
    URI_PORT = OptionItem(7, "Uri-Port", INTEGER, False, 5683)
    LOCATION_PATH = OptionItem(8, "Location-Path", STRING, True, None)
    URI_PATH = OptionItem(11, "Uri-Path", STRING, True, None)
    CONTENT_TYPE = OptionItem(12, "Content-Type", INTEGER, False, 0)
    MAX_AGE = OptionItem(14, "Max-Age", INTEGER, False, 60)
    URI_QUERY = OptionItem(15, "Uri-Query", STRING, True, None)
    ACCEPT = OptionItem(17, "Accept", INTEGER, False, 0)
    LOCATION_QUERY = OptionItem(20, "Location-Query", STRING, True, None)
    BLOCK2 = OptionItem(23, "Block2", INTEGER, False, None)
    BLOCK1 = OptionItem(27, "Block1", INTEGER, False, None)
    SIZE2 = OptionItem(28, "Size2", INTEGER, False, 0)
    PROXY_URI = OptionItem(35, "Proxy-Uri", STRING, False, None)
    PROXY_SCHEME = OptionItem(39, "Proxy-Schema", STRING, False, None)
    SIZE1 = OptionItem(60, "Size1", INTEGER, False, None)
    NO_RESPONSE = OptionItem(258, "No-Response", INTEGER, False, None)
    RM_MESSAGE_SWITCHING = OptionItem(65524, "Routing", OPAQUE, False, None)

    OCF_ACCEPT_CONTENT_FORMAT_VERSION = OptionItem(2049, "OCF-Accept-Content-Format-Version", INTEGER, False, None)
    OCF_CONTENT_FORMAT_VERSION = OptionItem(2053, "OCF-Content-Format-Version", INTEGER, False, None)

    # RFC8323 TCP/TLS/WebSockets Transports for CoAP
    MAX_MESSAGE_SIZE = OptionItem(2, "Max-Message-Size", INTEGER, False, 1152)
    BLOCK_WISE_TRANSFER = OptionItem(4, "Block-Wise-Transfer", INTEGER, False, 0)

    LIST = {
        0: RESERVED,
        1: IF_MATCH,
        3: URI_HOST,
        4: ETAG,
        5: IF_NONE_MATCH,
        6: OBSERVE,
        7: URI_PORT,
        8: LOCATION_PATH,
        11: URI_PATH,
        12: CONTENT_TYPE,
        14: MAX_AGE,
        15: URI_QUERY,
        17: ACCEPT,
        20: LOCATION_QUERY,
        23: BLOCK2,
        27: BLOCK1,
        28: SIZE2,
        35: PROXY_URI,
        39: PROXY_SCHEME,
        60: SIZE1,
        258: NO_RESPONSE,
        2049: OCF_ACCEPT_CONTENT_FORMAT_VERSION,
        2053: OCF_CONTENT_FORMAT_VERSION,
        65524: RM_MESSAGE_SWITCHING,

        2: MAX_MESSAGE_SIZE
    }

    @staticmethod
    def get_option_flags(option_num):
        """
        Get Critical, UnSafe, NoCacheKey flags from the option number
        as per RFC 7252, section 5.4.6

        :param option_num: option number
        :return: option flags
        :rtype: 3-tuple (critical, unsafe, no-cache)
        """
        opt_bytes = bytearray(2)
        if option_num < 256:
            s = struct.Struct("!B")
            s.pack_into(opt_bytes, 0, option_num)
        else:
            s = struct.Struct("H")
            s.pack_into(opt_bytes, 0, option_num)
        critical = (opt_bytes[0] & 0x01) > 0
        unsafe = (opt_bytes[0] & 0x02) > 0
        nocache = ((opt_bytes[0] & 0x1e) == 0x1c)
        return (critical, unsafe, nocache)


Types = {
    'CON': 0,
    'NON': 1,
    'ACK': 2,
    'RST': 3,
    'None': None
}


class MsgType(Enum):
    CON = 0
    NON = 1
    ACK = 2
    RST = 3
    NONE = None


CodeItem = collections.namedtuple('CodeItem', 'number name')


class Codes(object):
    """
    CoAP codes. Every code is represented as (NUMBER, NAME)
    """
    ERROR_LOWER_BOUND = 128

    EMPTY = CodeItem(0, 'EMPTY')
    GET = CodeItem(1, 'GET')
    POST = CodeItem(2, 'POST')
    PUT = CodeItem(3, 'PUT')
    DELETE = CodeItem(4, 'DELETE')

    CREATED = CodeItem(65, 'CREATED')
    DELETED = CodeItem(66, 'DELETED')
    VALID = CodeItem(67, 'VALID')
    CHANGED = CodeItem(68, 'CHANGED')
    CONTENT = CodeItem(69, 'CONTENT')
    CONTINUE = CodeItem(95, 'CONTINUE')

    BAD_REQUEST = CodeItem(128, 'BAD_REQUEST')
    FORBIDDEN = CodeItem(131, 'FORBIDDEN')
    NOT_FOUND = CodeItem(132, 'NOT_FOUND')
    METHOD_NOT_ALLOWED = CodeItem(133, 'METHOD_NOT_ALLOWED')
    NOT_ACCEPTABLE = CodeItem(134, 'NOT_ACCEPTABLE')
    REQUEST_ENTITY_INCOMPLETE = CodeItem(136, 'REQUEST_ENTITY_INCOMPLETE')
    PRECONDITION_FAILED = CodeItem(140, 'PRECONDITION_FAILED')
    REQUEST_ENTITY_TOO_LARGE = CodeItem(141, 'REQUEST_ENTITY_TOO_LARGE')
    UNSUPPORTED_CONTENT_FORMAT = CodeItem(143, 'UNSUPPORTED_CONTENT_FORMAT')

    INTERNAL_SERVER_ERROR = CodeItem(160, 'INTERNAL_SERVER_ERROR')
    NOT_IMPLEMENTED = CodeItem(161, 'NOT_IMPLEMENTED')
    BAD_GATEWAY = CodeItem(162, 'BAD_GATEWAY')
    SERVICE_UNAVAILABLE = CodeItem(163, 'SERVICE_UNAVAILABLE')
    GATEWAY_TIMEOUT = CodeItem(164, 'GATEWAY_TIMEOUT')
    PROXY_NOT_SUPPORTED = CodeItem(165, 'PROXY_NOT_SUPPORTED')

    # RFC8323 TCP/TLS/WebSockets Transports for CoAP
    CSM = CodeItem(225, 'CSM')
    PING = CodeItem(226, 'PING')
    PONG = CodeItem(227, 'PONG')
    RELEASE = CodeItem(228, 'RELEASE')
    ABORT = CodeItem(229, 'ABORT')

    LIST = {
        0: EMPTY,
        1: GET,
        2: POST,
        3: PUT,
        4: DELETE,

        65: CREATED,
        66: DELETE,
        67: VALID,
        68: CHANGED,
        69: CONTENT,
        95: CONTINUE,

        128: BAD_REQUEST,
        131: FORBIDDEN,
        132: NOT_FOUND,
        133: METHOD_NOT_ALLOWED,
        134: NOT_ACCEPTABLE,
        136: REQUEST_ENTITY_INCOMPLETE,
        140: PRECONDITION_FAILED,
        141: REQUEST_ENTITY_TOO_LARGE,
        143: UNSUPPORTED_CONTENT_FORMAT,

        160: INTERNAL_SERVER_ERROR,
        161: NOT_IMPLEMENTED,
        162: BAD_GATEWAY,
        163: SERVICE_UNAVAILABLE,
        164: GATEWAY_TIMEOUT,
        165: PROXY_NOT_SUPPORTED,

        225: CSM,
        226: PING,
        227: PONG,
        228: RELEASE,
        229: ABORT

    }

    @staticmethod
    def class_code(code):
        return int(f'{code:08b}'[:3], 2)

    @classmethod
    def is_error(cls, code):
        class_code = cls.class_code(code)
        return class_code in [4, 5]


Content_types = {
    "text/plain": 0,
    "application/link-format": 40,
    "application/xml": 41,
    "application/octet-stream": 42,
    "application/exi": 47,
    "application/json": 50,
    "application/cbor": 60,
    "application/vnd.ocf+cbor": 10000
    #                 0: 'text/plain;charset=utf-8',
    #                16: 'application/cose;cose-type="cose-encrypt0"',
    #                17: 'application/cose;cose-type="cose-mac0"',
    #                18: 'application/cose;cose-type="cose-sign1"',
    #                40: 'application/link-format',
    #                41: 'application/xml',
    #                42: 'application/octet-stream',
    #                47: 'application/exi',
    #                50: 'application/json',
    #                51: 'application/json-patch+json',
    #                52: 'application/merge-patch+json',
    #                60: 'application/cbor',
    #                61: 'application/cwt',
    #                62: 'application/multipast-core', # draft-ietf-core-multipart-ct
    #                64: 'application/link-format+cbor', # draft-ietf-core-links-json-10
    #                70: 'application/oscon', # draft-ietf-core-object-security-01
    #                96: 'application/cose;cose-type="cose-encrypt"',
    #                97: 'application/cose;cose-type="cose-mac"',
    #                98: 'application/cose;cose-type="cose-sign"',
    #                101: 'application/cose-key',
    #                102: 'application/cose-key-set',
    #                110: 'application/senml+json',
    #                111: 'application/sensml+json',
    #                112: 'application/senml+cbor',
    #                113: 'application/sensml+cbor',
    #                114: 'application/senml-exi',
    #                115: 'application/sensml-exi',
    #                256: 'application/coap-group+json',
    #                280: 'application/pkcs7-mime;smime-type=server-generated-key',
    #                281: 'application/pkcs7-mime;smime-type=certs-only',
    #                282: 'application/pkcs7-mime;smime-type=CMC-Request',
    #                283: 'application/pkcs7-mime;smime-type=CMC-Response',
    #                284: 'application/pkcs8',
    #                285: 'application/csrattrs',
    #                286: 'application/pkcs10',
    #                310: 'application/senml+xml',
    #                311: 'application/sensml+xml',
    #                1000: 'application/vnd.ocf+cbor',
    #                11542: 'application/vnd.oma.lwm2m+tlv',
    #                11543: 'application/vnd.oma.lwm2m+json',
    #                504: 'application/link-format+json', # draft-ietf-core-links-json-10
}

COAP_PREFACE = "coap://"
LOCALHOST = "127.0.0.1"
HC_PROXY_DEFAULT_PORT = 8080  # TODO there is a standard for this?
COAP_DEFAULT_PORT = 5683
DEFAULT_HC_PATH = "/"
BAD_REQUEST = 400  # "Bad Request" error code
NOT_IMPLEMENTED = 501  # "Not Implemented" error code

# Dictionary to map CoAP to HTTP requests code
CoAP_HTTP = {

    "CREATED": "201",
    "DELETED": "200",
    "VALID": "304",
    "CHANGED": "200",
    "CONTENT": "200",
    "BAD_REQUEST": "400",
    "FORBIDDEN": "403",
    "NOT_FOUND": "404",
    "METHOD_NOT_ALLOWED": "400",
    "NOT_ACCEPTABLE": "406",
    "PRECONDITION_FAILED": "412",
    "REQUEST_ENTITY_TOO_LARGE": "413",
    "UNSUPPORTED_CONTENT_FORMAT": "415",
    "INTERNAL_SERVER_ERROR": "500",
    "NOT_IMPLEMENTED": "501",
    "BAD_GATEWAY": "502",
    "SERVICE_UNAVAILABLE": "503",
    "GATEWAY_TIMEOUT": "504",
    "PROXY_NOT_SUPPORTED": "502"
}
