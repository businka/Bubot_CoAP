import asyncio
import logging
from Bubot_CoAP.messages.request import Request
from Bubot_CoAP.messages.response import Response

logger = logging.getLogger(__name__)


class CallbackLayer:
    def __init__(self):
        self._waited_answer = {}

    async def wait(self, request: Request, **kwargs):
        timeout = kwargs.get('timeout', 20)
        waiter = Waiter(request, **kwargs)
        self._waited_answer[waiter.key] = waiter
        try:
            return await asyncio.wait_for(waiter.future, timeout)
        except asyncio.CancelledError:
            waiter.future.set_exception(asyncio.CancelledError())
        except asyncio.TimeoutError:
            waiter.future.set_exception(asyncio.TimeoutError())
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

    @property
    def key(self):
        return self._request.token

    @property
    def future(self):
        return self._future

    @future.setter
    def future(self, value: Response):
        self._future.set_result(value)
