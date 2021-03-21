import logging
from urllib.parse import SplitResult

logger = logging.getLogger(__name__)


class Endpoint:
    _scheme = None

    @staticmethod
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

    @staticmethod
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
