import gzip
from collections.abc import Coroutine
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


class GzipRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, '_body'):
            body = await super().body()
            if 'gzip' in self.headers.getlist('Content-Encoding'):
                body = gzip.decompress(body)
            self._body = body  # pylint: disable=attribute-defined-outside-init
        return self._body


class GzipRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
