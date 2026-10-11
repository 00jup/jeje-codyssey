#!/usr/bin/env python3
"""
로컬 개발 서버.

Vercel 배포 환경에서는 `api/*.py` 를 플랫폼이 알아서 함수로 띄우고, 정적 파일은
CDN이 서빙하며, `vercel.json` 의 `rewrites` 가 5자 짧은 링크를 `read.html` 로
돌린다. 로컬에는 그 플랫폼이 없으므로 이 서버가 세 가지를 대신한다:

    python3 dev_server.py          # http://localhost:3000

`vercel dev` 를 쓸 수 있으면 그쪽이 배포 환경에 더 가깝다. 이 파일은 Node/Vercel
CLI 없이도 돌려볼 수 있게 두는 것이고, 프론트엔드 코드는 양쪽에서 한 줄도
다르지 않다.
"""

from __future__ import annotations

import os
import re
import sys
from urllib.parse import unquote, urlsplit
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))

# .env 를 읽는다. 배포 환경에서는 Vercel 이 환경 변수를 직접 넣어주므로 이 코드가
# 서버리스 함수 쪽에는 없다 — 로컬에만 필요한 편의다.
env_path = os.path.join(ROOT, ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import compose  # noqa: E402  (경로를 먼저 잡아야 import 가 된다)
import letter  # noqa: E402

ROUTES = {"/api/compose": compose.handler, "/api/letter": letter.handler}

# vercel.json 의 rewrite 규칙과 정확히 같은 패턴 — 무작위든 커스텀이든
# 짧은 링크(3~20자)를 read.html 로.
SHORT_LINK_RE = re.compile(r"^/[a-z0-9][a-z0-9-]{1,18}[a-z0-9]$")


class Dev(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):  # noqa: N802
        path_only = unquote(urlsplit(self.path).path)
        if any(part.startswith(".") for part in path_only.split("/") if part):
            self.send_error(404)
            return
        if path_only in ROUTES:
            self._proxy("do_GET")
            return
        if SHORT_LINK_RE.match(path_only):
            # 배포 환경의 vercel.json rewrite 를 흉내 낸다 — 주소창은 그대로
            # 두고 read.html 을 대신 서빙한다.
            self.path = "/read.html"
        super().do_GET()

    def do_POST(self):  # noqa: N802
        self._proxy("do_POST")

    def _proxy(self, method: str):
        route = ROUTES.get(self.path.split("?")[0])
        if not route:
            self.send_error(404, "no such endpoint")
            return
        # 핸들러를 `__init__` 없이 만들고, 소켓·헤더만 이쪽 것으로 빌려준다.
        # BaseHTTPRequestHandler 의 `__init__` 은 생성되는 순간 요청을 다시 파싱하며
        # 통신까지 해버리므로 정상 생성하면 연결을 두 번 잡는 꼴이 된다.
        proxy = route.__new__(route)
        proxy.path = self.path
        proxy.headers = self.headers
        proxy.rfile = self.rfile
        proxy.wfile = self.wfile
        proxy.request_version = self.request_version
        proxy.send_response = self.send_response
        proxy.send_header = self.send_header
        proxy.end_headers = super().end_headers
        getattr(proxy, method)()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    print(f"거부불가 로컬 서버 → http://localhost:{port}")
    missing = [k for k in ("ANTHROPIC_API_KEY",
                            "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN")
               if not os.environ.get(k)]
    if missing:
        print(f"경고: {', '.join(missing)} 가 없다. 관련 기능은 오류를 돌려준다.")
    ThreadingHTTPServer(("127.0.0.1", port), Dev).serve_forever()
