from .udp import UdpCoapEndpoint
# from .udp_tls2 import UdpCoapsEndpoint  #pydtls
from .udp_tls import UdpCoapsEndpoint  # aio-dtls
from .endpoint import Endpoint

supported_scheme = {
    'coap': UdpCoapEndpoint,
    'coaps': UdpCoapsEndpoint
}
