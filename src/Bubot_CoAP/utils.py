# -*- coding: utf-8 -*-
import asyncio
import binascii
import random
from socket import AF_INET, AF_INET6, getaddrinfo
from urllib.parse import urlparse, SplitResult

__author__ = 'Giacomo Tanganelli'


def calc_family_by_address(address):
    if address[0] == '' or address[0] is None:
        family = AF_INET
        address = ('', address[1])
    elif address[0] == '::':
        family = AF_INET6
        address = ('[::]', address[1])
    else:
        family = getaddrinfo(address[0], address[1])[0][0]
        address = address
    return family, address


def str_append_hash(*args):
    """ Convert each argument to a lower case string, appended, then hash """
    ret_hash = ""
    for i in args:
        if isinstance(i, (str, int)):
            ret_hash += str(i).lower()
        elif isinstance(i, bytes):
            ret_hash += binascii.hexlify(i).decode("utf-8")

    return hash(ret_hash)


def check_nocachekey(option):
    """
    checks if an option is a NoCacheKey option or Etag

    :param option:
    :return:
    """
    return ((option.number & 0x1E) == 0x1C) | (option.number == 4)


def check_code(code):
    """
    checks if the response code is one of the valid ones defined in the rfc

    :param code:
    :return:
    """
    if (65 <= code <= 69) or (128 <= code <= 134) or (code == 140) or (code == 141) or (code == 143) or (
            160 <= code <= 165):
        return

    else:
        raise InvalidResponseCode


"""
exception used to signal an invalid response code
"""


class InvalidResponseCode:
    def __init__(self, code):
        self.inv_code = code


def is_uri_option(number):
    """
    checks if the option is part of uri-path, uri-host, uri-port, uri-query

    :param number:
    :return:
    """
    if number == 3 | number == 7 | number == 11 | number == 15:
        return True
    return False


def generate_random_token(size):
    return bytes([random.randint(0, 255) for _ in range(size)])


def parse_blockwise(value):
    """
    Parse Blockwise option.

    :param value: option value
    :return: num, m, size
    """

    length = byte_len(value)
    if length == 1:
        num = value & 0xF0
        num >>= 4
        m = value & 0x08
        m >>= 3
        size = value & 0x07
    elif length == 2:
        num = value & 0xFFF0
        num >>= 4
        m = value & 0x0008
        m >>= 3
        size = value & 0x0007
    else:
        num = value & 0xFFFFF0
        num >>= 4
        m = value & 0x000008
        m >>= 3
        size = value & 0x000007
    return num, int(m), pow(2, (size + 4))


def byte_len(int_type):
    """
    Get the number of byte needed to encode the int passed.

    :param int_type: the int to be converted
    :return: the number of bits needed to encode the int passed.
    """
    length = 0
    while int_type:
        int_type >>= 1
        length += 1
    if length > 0:
        if length % 8 != 0:
            length = int(length / 8) + 1
        else:
            length = int(length / 8)
    return length


def host_port_join(host, port=None):
    """Join a host and optionally port into a hostinfo-style host:port
    string

    >> host_port_join('example.com')
    'example.com'
    >> host_port_join('example.com', 1234)
    'example.com:1234'
    >> host_port_join('127.0.0.1', 1234)
    '127.0.0.1:1234'

    This is lax with respect to whether host is an IPv6 literal in brackets or
    not, and accepts either form; IP-future literals that do not contain a
    colon must be already presented in their bracketed form:

    >> host_port_join('2001:db8::1')
    '[2001:db8::1]'
    >> host_port_join('2001:db8::1', 1234)
    '[2001:db8::1]:1234'
    >> host_port_join('[2001:db8::1]', 1234)
    '[2001:db8::1]:1234'
    """
    if ':' in host and not (host.startswith('[') and host.endswith(']')):
        host = f'[{host}]'

    if port is None:
        hostinfo = host
    else:
        hostinfo = f'{host}:{port}'
    return hostinfo


def host_port_split(host_port):
    """Like urllib.parse.splitport, but return port as int, and as None if not
    given. Also, it allows giving IPv6 addresses like a netloc:

    >> host_port_split('foo')
    ('foo', None)
    >> host_port_split('foo:5683')
    ('foo', 5683)
    >> host_port_split('[::1%eth0]:56830')
    ('::1%eth0', 56830)
    """

    pseudoparsed = SplitResult(None, host_port, None, None, None)
    try:
        return pseudoparsed.hostname, pseudoparsed.port
    except ValueError:
        if '[' not in host_port and host_port.count(':') > 1:
            raise ValueError("Could not parse network location. "
                             "Beware that when IPv6 literals are expressed in URIs, they "
                             "need to be put in square brackets to distinguish them from "
                             "port numbers.")
        raise


def parse_uri2(uri):
    url = urlparse(uri)
    host, port = host_port_split(url.netloc)
    return {'scheme': url.scheme, 'address': (host, port)}


def parse_uri(uri):
    t = uri.split("://")
    tmp = t[1]
    t = tmp.split("/", 1)
    tmp = t[0]
    path = t[1]
    if tmp.startswith("["):
        t = tmp.split("]")
        host = t[0][1:]
        port = int(t[1][1:])
    else:
        t = tmp.split(":", 1)
        try:
            host = t[0]
            port = int(t[1])
        except IndexError:
            host = tmp
            port = 5683

    return str(host), port, path


def create_logging():  # pragma: no cover
    with open("logging.conf", "w") as f:
        f.writelines("[loggers]\n")
        f.writelines("keys=root\n\n")
        f.writelines("[handlers]\n")
        f.writelines("keys=consoleHandler\n\n")
        f.writelines("[formatters]\n")
        f.writelines("keys=simpleFormatter\n\n")
        f.writelines("[logger_root]\n")
        f.writelines("level=DEBUG\n")
        f.writelines("handlers=consoleHandler\n\n")
        f.writelines("[handler_consoleHandler]\n")
        f.writelines("class=StreamHandler\n")
        f.writelines("level=DEBUG\n")
        f.writelines("formatter=simpleFormatter\n")
        f.writelines("args=(sys.stdout,)\n\n")
        f.writelines("[formatter_simpleFormatter]\n")
        f.writelines("format=%(asctime)s - %(threadName)-10s - %(name)s - %(levelname)s - %(message)s\n")
        f.writelines("datefmt=")


class Tree(object):
    def __init__(self):
        self.tree = {}

    def dump(self):
        """
        Get all the paths registered in the server.

        :return: registered resources.
        """
        return sorted(list(self.tree.keys()))

    def with_prefix(self, path):
        ret = []
        for key in list(self.tree.keys()):
            if path.startswith(key):
                ret.append(key)

        if len(ret) > 0:
            return ret
        raise KeyError

    def with_prefix_resource(self, path):
        ret = []
        for key, value in self.tree.items():
            if path.startswith(key):
                ret.append(value)

        if len(ret) > 0:
            return ret
        raise KeyError

    def __getitem__(self, item):
        return self.tree[item]

    def __setitem__(self, key, value):
        self.tree[key] = value

    def __delitem__(self, key):
        del self.tree[key]

    def __contains__(self, item):
        return item in self.tree


# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""Tools not directly related with CoAP that are needed to provide the API"""


class ExtensibleEnumMeta(type):
    """Metaclass for ExtensibleIntEnum, see there for detailed explanations"""

    def __init__(self, name, bases, dict):
        self._value2member_map_ = {}
        for k, v in dict.items():
            if k.startswith('_'):
                continue
            if callable(v):
                continue
            if isinstance(v, property):
                continue
            instance = self(v)
            instance.name = k
            setattr(self, k, instance)
        type.__init__(self, name, bases, dict)

    def __call__(self, value):
        if isinstance(value, self):
            return value
        if value not in self._value2member_map_:
            self._value2member_map_[value] = super(ExtensibleEnumMeta, self).__call__(value)
        return self._value2member_map_[value]


class ExtensibleIntEnum(int, metaclass=ExtensibleEnumMeta):
    """Similar to Python3.4's enum.IntEnum, this type can be used for named
    numbers which are not comprehensively known, like CoAP option numbers."""

    def __add__(self, delta):
        return type(self)(int(self) + delta)

    def __repr__(self):
        return '<%s %d%s>' % (type(self).__name__, self, ' "%s"' % self.name if hasattr(self, "name") else "")

    def __str__(self):
        return self.name if hasattr(self, "name") else int.__str__(self)


def hostportjoin(host, port=None):
    """Join a host and optionally port into a hostinfo-style host:port
    string"""
    if ':' in host:
        host = '[%s]' % host

    if port is None:
        hostinfo = host
    else:
        hostinfo = "%s:%d" % (host, port)
    return hostinfo


class Timer:
    def __init__(self, interval, callback, params):
        self._ok = True
        self._task = asyncio.create_task(self._job(interval, callback, params))

    async def _job(self, interval, callback, params):
        try:
            while self._ok:
                await asyncio.sleep(interval)
                await callback(*params)
        except asyncio.CancelledError:
            return

    async def cancel(self):
        self._ok = False
        self._task.cancel()
        await self._task
