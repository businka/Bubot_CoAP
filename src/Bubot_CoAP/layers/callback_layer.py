import asyncio
import logging

from bubot_helpers.ExtException import ExtException
from ..messages.request import Request
from ..messages.response import Response

logger = logging.getLogger('Bubot_CoAP')
from ..defines import MULTICAST_TIMEOUT


class CallbackLayer:
    def __init__(self, server):
        self.server = server
        self._waited_answer = {}

    async def wait(self, request: Request, *, timeout=None, **kwargs):
        # timeout = kwargs.get('timeout')
        try:
            if not timeout:
                timeout = MULTICAST_TIMEOUT
            waiter = Waiter(request, **kwargs)
            self._waited_answer[waiter.key] = waiter
            try:
                result = await asyncio.wait_for(waiter.future, timeout)
                return result
            except (asyncio.TimeoutError, asyncio.CancelledError) as err:
                if request.multicast:
                    return waiter.result
                else:
                    raise err
            except Exception as err:
                raise err
            finally:
                self._waited_answer.pop(waiter.key, None)
            pass
        except (asyncio.TimeoutError, asyncio.CancelledError) as err:
            raise err
        except Exception as err:
            raise ExtException(parent=err)

    def set_result(self, response: Response):
        try:
            waiter = self._waited_answer[response.token]
        except KeyError:
            logger.warning(f'awaited request not found {response}')
            return
        logger.debug(f'return_response - {response}')
        waiter.future = response
        pass

    def cancel_waited(self, exception):
        for key in list(self._waited_answer.keys()):
            waiter = self._waited_answer.pop(key, None)
            if not waiter.future.done():
                waiter.future.set_exception(exception)


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
