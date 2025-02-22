import copy
import logging
from ..messages.request import Request
from ..example.coapclient import HelperClient
from ..messages.response import Response
from .. import defines
from .. resources import RemoteResource
from ..utils import parse_uri

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class ForwardLayer(object):
    """
    Class used by Proxies to forward messages.
    """
    def __init__(self, server):
        self._server = server

    def receive_request(self, transaction):
        """
        Setup the transaction for forwarding purposes on Forward Proxies.
         
        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction
        """
        uri = transaction.request.proxy_uri
        if uri is None:
            transaction.response = Response.init_from_request(transaction.request)
            transaction.response.type = defines.Types["RST"]
            transaction.response.code = defines.Codes.BAD_REQUEST.number
            return transaction

        host, port, path = parse_uri(uri)
        path = str("/" + path)
        transaction.response = Response.init_from_request(transaction.request)
        return self._forward_request(transaction, (host, port), path)

    def receive_request_reverse(self, transaction):
        """
        Setup the transaction for forwarding purposes on Reverse Proxies.
         
        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction
        """
        wkc_resource_is_defined = defines.DISCOVERY_URL in self._server.root
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response.init_from_request(transaction.request)
        if path == defines.DISCOVERY_URL and not wkc_resource_is_defined:
            transaction = self._server.resource_layer.discover(transaction)
        else:
            new = False
            if transaction.request.code == defines.Codes.POST.number:
                new_paths = self._server.root.with_prefix(path)
                new_path = "/"
                for tmp in new_paths:
                    if len(tmp) > len(new_path):
                        new_path = tmp
                if path != new_path:
                    new = True
                path = new_path
            try:
                resource = self._server.root[path]
            except KeyError:
                resource = None
            if resource is None or path == '/':
                # Not Found
                transaction.response.code = defines.Codes.NOT_FOUND.number
            else:
                transaction.resource = resource
                transaction = self._handle_request(transaction, new)
        return transaction

    @staticmethod
    def _forward_request(transaction, destination, path):
        """
        Forward requests.

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :param destination: the destination of the request (IP, port)
        :param path: the path of the request.
        :rtype : Transaction
        :return: the edited transaction
        """
        client = HelperClient(destination)
        request = Request()
        request.options = copy.deepcopy(transaction.request.options)
        del request.block2
        del request.block1
        del request.uri_path
        del request.proxy_uri
        del request.proxy_schema
        # TODO handle observing
        del request.observe
        # request.observe = transaction.request.observe

        request.uri_path = path
        request.destination = destination
        request.payload = transaction.request.payload
        request.code = transaction.request.code
        response = client.send_request(request)
        client.stop()
        if response is not None:
            transaction.response.payload = response.payload
            transaction.response.code = response.code
            transaction.response.options = response.options
        else:
            transaction.response.code = defines.Codes.SERVICE_UNAVAILABLE.number

        return transaction

    def _handle_request(self, transaction, new_resource):
        """
        Forward requests. Used by reverse proxies to also create new virtual resources on the proxy 
        in case of created resources
        
        :type new_resource: bool
        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :param new_resource: if the request will generate a new resource 
        :return: the edited transaction
        """
        client = HelperClient(transaction.resource.remote_server)
        request = Request()
        request.options = copy.deepcopy(transaction.request.options)
        del request.block2
        del request.block1
        del request.uri_path
        del request.proxy_uri
        del request.proxy_schema
        # TODO handle observing
        del request.observe
        # request.observe = transaction.request.observe

        request.uri_path = "/".join(transaction.request.uri_path.split("/")[1:])
        request.destination = transaction.resource.remote_server
        request.payload = transaction.request.payload
        request.code = transaction.request.code
        logger.info("forward_request - " + str(request))
        response = client.send_request(request)
        client.stop()
        logger.info("forward_response - " + str(response))
        transaction.response.payload = response.payload
        transaction.response.code = response.code
        transaction.response.options = response.options
        if response.code == defines.Codes.CREATED.number:
            lp = transaction.response.location_path
            del transaction.response.location_path
            transaction.response.location_path = transaction.request.uri_path.split("/")[0] + "/" + lp
            # TODO handle observing
            if new_resource:
                resource = RemoteResource('server', transaction.resource.remote_server, lp, coap_server=self,
                                          visible=True,
                                          observable=False,
                                          allow_children=True)
                self._server.add_resource(transaction.response.location_path, resource)
        if response.code == defines.Codes.DELETED.number:
            del self._server.root["/" + transaction.request.uri_path]
        return transaction
