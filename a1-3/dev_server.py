#!/usr/bin/env python3
"""
로컬 개발 서버.

Vercel 배포 환경에서는 `api/*.py` 를 플랫폼이 알아서 함수로 띄우고 정적 파일은
CDN 이 서빙한다. 로컬에는 그 플랫폼이 없으므로, **같은 핸들러 클래스**를 그대로
불러다 붙여 배포와 같은 경로(`/api/draft`, `/api/reply`)로 답하게 한다.

    python3 dev_server.py          # http://localhost:3000

`vercel dev` 를 쓸 수 있으면 그쪽이 배포 환경에 더 가깝다. 이 파일은 Node/Vercel CLI
없이도 돌려볼 수 있게 두는 것이고, 프론트엔드 코드는 양쪽에서 한 줄도 다르지 않다.
"""

from __future__ import annotations

import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))

# .env 를 읽는다. 배포 환경에서는 Vercel 이 환경 변수를 직접 넣어주므로 이 코드가
# 서버리스 함수 쪽에는 없다 — 로컬에만 필요한 편의다.
#
# a1-3/.env 가 없으면 같은 저장소의 b2-2/.env 를 본다. 이 저장소의 과제들이 같은
# Gemini 키를 쓰고 있어서, 과제마다 키를 복사해 두면 폐기할 때 하나를 빠뜨리게 된다.
# 두 파일 모두 .gitignore 에 있고 값을 출력하지 않는다.
for env_path in (os.path.join(ROOT, ".env"),
                 os.path.join(os.path.dirname(ROOT), "b2-2", ".env")):
    if not os.path.exists(env_path):
        continue
    with open(env_path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    if os.environ.get("GEMINI_API_KEY"):
        break

import draft  # noqa: E402  (경로를 먼저 잡아야 import 가 된다)
import reply  # noqa: E402

ROUTES = {"/api/draft": draft.handler, "/api/reply": reply.handler}


class Dev(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):  # noqa: N802
        # 배포 환경에서는 `/api/*` 로 오는 GET 을 함수가 받아 405 를 준다. 로컬에서도
        # 같게 답해야 "여긴 POST 전용" 이라는 사실이 양쪽에서 일치한다.
        if self.path.split("?")[0] in ROUTES:
            self._proxy("do_GET")
            return
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
    print(f"타래공방 로컬 서버 → http://localhost:{port}")
    if not os.environ.get("GEMINI_API_KEY"):
        print("경고: GEMINI_API_KEY 가 없다. AI 기능은 500 을 돌려준다.")
    ThreadingHTTPServer(("0.0.0.0", port), Dev).serve_forever()
