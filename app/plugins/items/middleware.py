from starlette.middleware.base import BaseHTTPMiddleware


class ItemsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Items-Plugin"] = "enabled"
        return response