import asyncio
import logging
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.response import Response

logger = logging.getLogger(__name__)
from Bubot_CoAP.defines import MULTICAST_TIMEOUT


class CallbackLayer:
    def __init__(self, server):
        self.server = server
        self._waited_answer = {}

    async def wait(self, request: Request, **kwargs):
        timeout = kwargs.get('timeout')
        if not timeout:
            timeout = MULTICAST_TIMEOUT
        waiter = Waiter(request, **kwargs)
        self._waited_answer[waiter.key] = waiter
        try:
            return await asyncio.wait_for(waiter.future, timeout)
        except asyncio.CancelledError:
            waiter.future.set_exception(asyncio.CancelledError())
        except asyncio.TimeoutError:
            if request.multicast:
                return waiter.result
            else:
                raise asyncio.TimeoutError()
        finally:
            self._waited_answer.pop(waiter.key, None)
        pass

    def set_result(self, response: Response):
        try:
            waiter = self._waited_answer[response.token]
        except KeyError:
            logger.warning(f'awaited request not found {response}')
            return
        logger.debug(f'return_response - {response}')
        waiter.future = response
        pass


class Waiter:
    def __init__(self, request: Request, **kwargs):
        self._request = request
        self._future = asyncio.Future()
        self._result = []

    @property
    def key(self):
        return self._request.token

    @property
    def future(self):
        return self._future

    @future.setter
    def future(self, value: Response):
        if self._request.multicast:
            self._result.append(value)
        else:
            self._future.set_result(value)

    @property
    def result(self):
        return self._result
