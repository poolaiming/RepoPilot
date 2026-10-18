from __future__ import annotations

import ipaddress
import os
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.config import config_value


MAX_BODY_BYTES = 64 * 1024
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def repository_root(repo_path: str) -> Path:
    root = Path(repo_path).expanduser().resolve()
    configured = config_value("REPOPILOT_REPO_ROOTS")
    allowed = [Path(item).expanduser().resolve() for item in configured.split(os.pathsep) if item.strip()]
    if not allowed:
        raise ValueError("Set REPOPILOT_REPO_ROOTS to trusted repository roots in .env, then retry.")
    if not any(root.is_relative_to(base) for base in allowed):
        raise ValueError("Repository is outside REPOPILOT_REPO_ROOTS.")
    if not root.is_dir():
        raise ValueError("Repository directory does not exist.")
    return root


def local_request_error(request: Request) -> str | None:
    try:
        local_client = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
    except ValueError:
        local_client = False
    if not local_client:
        return "Local access only. Open http://127.0.0.1:8000 on this computer."
    host = request.url.hostname
    if host not in LOCAL_HOSTS:
        return "Use localhost or a loopback IP in the browser URL."
    if request.headers.get("sec-fetch-site") == "cross-site":
        return "Cross-site requests are blocked. Open RepoPilot directly."
    origin = request.headers.get("origin")
    if origin:
        expected = f"{request.url.scheme}://{request.headers.get('host', '')}"
        if origin != expected:
            return "Origin must match the RepoPilot address."
    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            return "Use application/json for this operation."
    return None


class LocalSecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        error = local_request_error(request)
        if error:
            await JSONResponse({"detail": error}, status_code=403)(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_BODY_BYTES:
                await JSONResponse({"detail": "Request body exceeds 64 KiB."}, status_code=413)(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
