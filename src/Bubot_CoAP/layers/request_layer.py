from ..messages.response import Response
from .. import defines

__author__ = 'Giacomo Tanganelli'


class RequestLayer(object):
    """
    Class to handle the Request/Response layer
    """
    def __init__(self, server):
        self._server = server

    async def receive_request(self, transaction):
        """
        Handle request and execute the requested method

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        method = transaction.request.code
        if method == defines.Codes.GET.number:
            transaction = await self._handle_get(transaction)
        elif method == defines.Codes.POST.number:
            transaction = await self._handle_post(transaction)
        elif method == defines.Codes.PUT.number:
            transaction = await self._handle_put(transaction)
        elif method == defines.Codes.DELETE.number:
            transaction = await self._handle_delete(transaction)
        else:
            transaction.response = None
        return transaction

    def send_request(self, request):
        """
         Dummy function. Used to do not broke the layered architecture.

        :type request: Request
        :param request: the request
        :return: the request unmodified
        """
        return request

    async def _handle_get(self, transaction):
        """
        Handle GET requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        wkc_resource_is_defined = defines.DISCOVERY_URL in self._server.root
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response.init_from_request(transaction.request)
        if path == defines.DISCOVERY_URL and not wkc_resource_is_defined:
            transaction = await self._server.resource_layer.discover(transaction)
        else:
            try:
                resource = self._server.root[path]
            except KeyError:
                resource = None
            if resource is None or path == '/':
                # Not Found
                transaction.response.code = defines.Codes.NOT_FOUND.number
            else:
                transaction.resource = resource
                transaction = await self._server.resource_layer.get_resource(transaction)
        return transaction

    async def _handle_put(self, transaction):
        """
        Handle PUT requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response.init_from_request(transaction.request)
        transaction.response.source = transaction.request.destination
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None
        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            transaction.resource = resource
            # Update request
            transaction = await self._server.resource_layer.update_resource(transaction)
        return transaction

    async def _handle_post(self, transaction):
        """
        Handle POST requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response.init_from_request(transaction.request)
        transaction.response.source = transaction.request.destination

        # Create request
        transaction = await self._server.resource_layer.create_resource(path, transaction)
        return transaction

    async def _handle_delete(self, transaction):
        """
        Handle DELETE requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response.init_from_request(transaction.request)
        transaction.response.source = transaction.request.destination
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None

        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            # Delete
            transaction.resource = resource
            transaction = await self._server.resource_layer.delete_resource(transaction, path)
        return transaction

