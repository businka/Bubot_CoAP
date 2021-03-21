
from .udp_coap import UdpCoapEndpoint
from .udp_coaps import UdpCoapsEndpoint
from .endpoint import Endpoint

supported_scheme = {
    'coap': UdpCoapEndpoint,
    'coaps': UdpCoapsEndpoint
}

