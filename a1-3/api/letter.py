"""
GET /api/letter?id=xxxxx — 저장된 편지 하나를 읽어 온다.

AI를 부르지 않는다. `compose.py` 가 만들 때 이미 편지 본문과 재치 대사를
같이 저장해 두었으므로, 여기서는 Upstash 조회 한 번이 전부다 — 받는 사람이
"거부" 버튼을 누르려 할 때마다 걸리는 지연이 없어야 하기 때문이다.
"""

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _shared import SHORT_ID_RE, ApiError, BaseHandler, kv_get


class handler(BaseHandler):  # noqa: N801
    def run_query(self, params: dict[str, list[str]]) -> dict[str, Any]:
        letter_id = (params.get("id") or [""])[0].strip().lower()
        if not letter_id or not SHORT_ID_RE.match(letter_id):
            raise ApiError(404, "NOT_FOUND", "이 편지는 사라졌거나 없는 편지입니다.")

        letter = kv_get(f"letter:{letter_id}")
        if not letter:
            raise ApiError(404, "NOT_FOUND", "이 편지는 사라졌거나 없는 편지입니다.")

        return {"letter": letter}
