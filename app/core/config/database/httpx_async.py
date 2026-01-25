# app.core.config.database.httpx_async.py
"""
    httpx AsyncClient - для внедрения зависисмости
    применение:
    http_client: httpx.AsyncClient = Depends(get_http_client)
"""


from fastapi import Request


async def get_http_client(request: Request):
    return request.app.state.http_client