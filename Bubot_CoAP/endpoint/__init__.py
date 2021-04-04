
from .udp import UdpCoapEndpoint
from .udp_tls import UdpCoapsEndpoint
from .endpoint import Endpoint

supported_scheme = {
    'coap': UdpCoapEndpoint,
    'coaps': UdpCoapsEndpoint
}

