# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""List of known values for the CoAP "Code" field.

The values in this module correspond to the IANA registry "`CoRE Parameters`_",
subregistries "CoAP Method Codes" and "CoAP Response Codes".

The codes come with methods that can be used to get their rough meaning, see
the :class:`Code` class for details.

.. _`CoRE Parameters`: https://www.iana.org/assignments/core-parameters/core-parameters.xhtml
"""

from ...utils import ExtensibleIntEnum

# COAP_CODE_EMPTY_MESSAGE = COAP_CODE(0,00),
#   COAP_CODE_GET = COAP_CODE(0,01),
#   COAP_CODE_POST = COAP_CODE(0,02),
#   COAP_CODE_PUT = COAP_CODE(0,03),
#   COAP_CODE_DELETE = COAP_CODE(0,04),
#   COAP_CODE_201_CREATED = COAP_CODE(2,01),
#   COAP_CODE_202_DELETED = COAP_CODE(2,02),
#   COAP_CODE_203_VALID = COAP_CODE(2,03),
#   COAP_CODE_204_CHANGED = COAP_CODE(2,04),
#   COAP_CODE_205_CONTENT = COAP_CODE(2,05),
#   COAP_CODE_231_CONTINUE = COAP_CODE(2,31),
#   COAP_CODE_400_BAD_REQUEST = COAP_CODE(4,00),
#   COAP_CODE_401_UNAUTHORIZED = COAP_CODE(4,01),
#   COAP_CODE_402_BAD_OPTION = COAP_CODE(4,02),
#   COAP_CODE_403_FORBIDDEN = COAP_CODE(4,03),
#   COAP_CODE_404_NOT_FOUND = COAP_CODE(4,04),
#   COAP_CODE_405_METHOD_NOT_ALLOWED = COAP_CODE(4,05),
#   COAP_CODE_406_NOT_ACCEPTABLE = COAP_CODE(4,06),
#   COAP_CODE_408_REQUEST_ENTITY_INCOMPLETE = COAP_CODE(4,08),
#   COAP_CODE_412_PRECONDITION_FAILED = COAP_CODE(4,12),
#   COAP_CODE_413_REQUEST_ENTITY_TOO_LARGE = COAP_CODE(4,13),
#   COAP_CODE_415_UNSUPPORTED_CONTENT_FORMAT = COAP_CODE(4,15),
#   COAP_CODE_500_INTERNAL_SERVER_ERROR = COAP_CODE(5,00),
#   COAP_CODE_501_NOT_IMPLEMENTED = COAP_CODE(5,01),
#   COAP_CODE_502_BAD_GATEWAY = COAP_CODE(5,02),
#   COAP_CODE_503_SERVICE_UNAVAILABLE = COAP_CODE(5,03),
#   COAP_CODE_504_GATEWAY_TIMEOUT = COAP_CODE(5,04),
#   COAP_CODE_505_PROXYING_NOT_SUPPORTED = COAP_CODE(5,05)
class Code(ExtensibleIntEnum):
    """Value for the CoAP "Code" field.

    As the number range for the code values is separated, the rough meaning of
    a code can be determined using the :meth:`is_request`, :meth:`is_response` and
    :meth:`is_successful` methods."""

    EMPTY = 0
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4
    FETCH = 5
    PATCH = 6
    iPATCH = 7
    CREATED = 65
    DELETED = 66
    VALID = 67
    CHANGED = 68
    CONTENT = 69
    CONTINUE = 95
    BAD_REQUEST = 128
    UNAUTHORIZED = 129
    BAD_OPTION = 130
    FORBIDDEN = 131
    NOT_FOUND = 132
    METHOD_NOT_ALLOWED = 133
    NOT_ACCEPTABLE = 134
    REQUEST_ENTITY_INCOMPLETE = 136
    CONFLICT = (4 << 5) + 9
    PRECONDITION_FAILED = 140
    REQUEST_ENTITY_TOO_LARGE = 141
    UNSUPPORTED_CONTENT_FORMAT = 143
    UNSUPPORTED_MEDIA_TYPE = UNSUPPORTED_CONTENT_FORMAT  # deprecated alias
    UNPROCESSABLE_ENTITY = (4 << 5) + 22
    INTERNAL_SERVER_ERROR = 160
    NOT_IMPLEMENTED = 161
    BAD_GATEWAY = 162
    SERVICE_UNAVAILABLE = 163
    GATEWAY_TIMEOUT = 164
    PROXYING_NOT_SUPPORTED = 165

    CSM = 225
    PING = 226
    PONG = 227
    RELEASE = 228
    ABORT = 229

    def is_request(self):
        """True if the code is in the request code range"""
        return True if 1 <= self < 32 else False

    def is_response(self):
        """True if the code is in the response code range"""
        return True if 64 <= self < 192 else False

    def is_error(self):
        """True if the code is in the response code range"""
        return True if 128 <= self < 224 else False

    def is_signalling(self):
        return True if self >= 224 else False

    def is_successful(self):
        """True if the code is in the successful subrange of the response code range"""
        return True if 64 <= self < 96 else False

    def can_have_payload(self):
        """True if a message with that code can carry a payload. This is not
        checked for strictly, but used as an indicator."""
        return self.is_response() or self in (self.POST, self.PUT, self.FETCH, self.PATCH, self.iPATCH)

    @property
    def class_(self):
        """The class of a code (distinguishing whether it's successful, a
        request or a response error or more).

        >>> Code.CONTENT
        <Successful Response Code 69 "2.05 Content">
        >>> Code.CONTENT.class_
        2
        >>> Code.BAD_GATEWAY
        <Response Code 162 "5.02 Bad Gateway">
        >>> Code.BAD_GATEWAY.class_
        5
        """
        return self >> 5

    @property
    def dotted(self):
        """The numeric value three-decimal-digits (c.dd) form"""
        return "%d.%02d" % divmod(self, 32)

    @property
    def name_printable(self):
        """The name of the code in human-readable form"""
        return self.name.replace('_', ' ').title()

    def __str__(self):
        if self.is_request() or self is self.EMPTY:
            return self.name
        elif self.is_response() or self.is_signalling():
            return "%s %s" % (self.dotted, self.name_printable)
        else:
            return "%d" % self

    def __repr__(self):
        """
        >>> Code.GET
        <Request Code 1 "GET">
        >>> Code.CONTENT
        <Successful Response Code 69 "2.05 Content">
        >>> Code.BAD_GATEWAY
        <Response Code 162 "5.02 Bad Gateway">
        >>> Code(32)
        <Code 32 "32">
        """
        return '<%s%sCode %d "%s">' % ("Successful " if self.is_successful() else "",
                                       "Request " if self.is_request() else "Response " if self.is_response() else "",
                                       self, self)

    name = property(lambda self: self._name if hasattr(self, "_name") else "(unknown)",
                    lambda self, value: setattr(self, "_name", value),
                    doc="The constant name of the code (equals name_printable readable in all-caps and with underscores)")


for k in vars(Code):
    if isinstance(getattr(Code, k), Code):
        locals()[k] = getattr(Code, k)

__all__ = ['Code'] + [k for (k, v) in locals().items() if isinstance(v, Code)]
