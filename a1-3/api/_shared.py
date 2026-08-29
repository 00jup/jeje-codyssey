"""
타래공방 서버리스 함수 공통 모듈.

Vercel Python 런타임은 `api/` 안의 각 `.py` 를 독립 함수로 만든다. 밑줄로 시작하는
파일은 라우트로 만들지 않으므로, 두 엔드포인트(`draft.py` / `reply.py`)가 공유하는
코드를 여기에 둔다. 번들에 함께 실리도록 `vercel.json` 의 `includeFiles` 에도
같은 경로를 적어 둔다.

여기가 아는 것: Gemini 호출, 입력 검증, 오류를 사람이 읽을 한국어로 바꾸기, HTTP 응답.
여기가 모르는 것: 어떤 글을 쓰는지(프롬프트는 각 엔드포인트에 있다).
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from typing import Any

# Vercel 번들에서 형제 모듈을 확실히 찾게 한다. 로컬 `vercel dev` 와 배포 환경의
# 작업 디렉터리가 달라서, 이 줄이 없으면 배포 후에만 ImportError 가 난다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── 오류 ──────────────────────────────────────────────────────────────────

class ApiError(Exception):
    """사용자에게 그대로 보여줄 수 있는 실패.

    화면에 띄울 문장을 서버가 정한다. 프론트가 상태 코드만 보고 문구를 지어내면
    같은 말을 두 군데서 관리하게 되고, 실제로 어긋난다.
    """

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def api_error_from(error: Exception) -> ApiError:
    """Gemini SDK 예외를 사람이 읽을 말로 바꾼다.

    원문은 `ClientError: 429 RESOURCE_EXHAUSTED ...` 같은 모양이라 그대로 화면에
    흘리면 사용자가 자기 입력을 의심한다. 실제로는 우리 쪽 한도 문제다.
    """
    status = getattr(error, "code", None) or getattr(error, "status_code", None)
    if status in (401, 403):
        return ApiError(502, "AUTH_ERROR",
                        "AI 서버 인증에 실패했습니다. 관리자에게 알려주세요.")
    if status == 429:
        return ApiError(429, "RATE_LIMIT",
                        "지금 요청이 몰렸습니다. 30초쯤 뒤에 다시 시도해 주세요.")
    if status == 400:
        return ApiError(400, "BAD_REQUEST",
                        "AI 서버가 요청을 거절했습니다. 입력을 조금 줄여서 다시 시도해 주세요.")
    if isinstance(status, int) and status >= 500:
        return ApiError(502, "UPSTREAM_ERROR",
                        "AI 서버가 응답하지 못했습니다. 잠시 후 다시 시도해 주세요.")
    return ApiError(502, "UNKNOWN",
                    "초안을 만들지 못했습니다. 잠시 후 다시 시도해 주세요.")


# ── 입력 검증 ─────────────────────────────────────────────────────────────

def josa(word: str, with_batchim: str, without: str) -> str:
    """받침에 맞는 조사를 고른다.

    "받은 댓글을(를)" 같은 괄호 표기는 안내문에서 눈에 걸린다. 한글 음절은
    (코드 - 0xAC00) % 28 이 0 이 아니면 받침이 있으므로 계산으로 정해진다.
    한글이 아닌 글자로 끝나면 받침 없는 쪽을 쓴다.
    """
    if not word:
        return without
    last = word[-1]
    if "\uac00" <= last <= "\ud7a3":
        return with_batchim if (ord(last) - 0xAC00) % 28 else without
    return without


def require_text(data: dict[str, Any], key: str, label: str, limit: int) -> str:
    """필수 문자열을 꺼낸다. 비면 400, 너무 길면 400.

    길이 상한은 UX 가 아니라 과금 방어다. 입력이 길수록 토큰이 늘고, 공개 URL 이라
    누구나 부를 수 있다.
    """
    value = str(data.get(key) or "").strip()
    if not value:
        raise ApiError(400, "EMPTY_INPUT",
                       f"{label}{josa(label, '을', '를')} 입력해 주세요.")
    if len(value) > limit:
        raise ApiError(400, "TOO_LONG",
                       f"{label}{josa(label, '은', '는')} {limit}자까지 넣을 수 있습니다. "
                       f"지금 {len(value)}자입니다.")
    return value


def optional_text(data: dict[str, Any], key: str, limit: int) -> str:
    value = str(data.get(key) or "").strip()
    return value[:limit]


def pick(data: dict[str, Any], key: str, allowed: dict[str, str], default: str) -> str:
    """선택지 값을 화이트리스트로 거른다.

    이 값들은 프롬프트 문장에 그대로 들어간다. 걸러내지 않으면 select 를 조작해
    임의 문장을 프롬프트에 심을 수 있다.
    """
    value = str(data.get(key) or "").strip()
    return allowed.get(value, allowed[default])


# ── Gemini ────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "gemini-3.7-flash"


def gemini_json(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Gemini 에 JSON 스키마를 주고 구조화 응답을 받는다.

    형식 위반은 한 번만 다시 시킨다. 두 번째도 실패하면 모델 문제가 아니라 입력이
    이상한 경우가 많아서, 계속 재시도해 봐야 요금만 든다.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ApiError(500, "NO_KEY",
                       "서버에 API 키가 설정되지 않았습니다. 관리자에게 알려주세요.")

    from google import genai  # 콜드 스타트를 줄이려고 함수 안에서 import 한다

    client = genai.Client(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL

    last: Exception | None = None
    for attempt in range(2):
        nudge = "" if attempt == 0 else "\n\n앞선 응답이 형식을 어겼다. 스키마를 정확히 지켜 다시 답하라."
        try:
            interaction = client.interactions.create(
                model=model,
                input=prompt + nudge,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
                store=False,
            )
        except Exception as error:  # SDK 예외 → 우리 말로
            raise api_error_from(error) from error

        raw = (interaction.output_text or "").strip()
        if not raw:
            last = ApiError(502, "EMPTY", "AI가 빈 응답을 돌려줬습니다.")
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            last = ValueError("최상위가 객체가 아니다")
        except json.JSONDecodeError as error:
            last = error

    raise ApiError(502, "BAD_SHAPE",
                   "AI 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.") from last


# ── HTTP ──────────────────────────────────────────────────────────────────

MAX_BODY = 64 * 1024


class JsonHandler(BaseHTTPRequestHandler):
    """POST 로 JSON 을 받아 JSON 을 돌려주는 핸들러의 공통 부분.

    하위 클래스는 `run(payload) -> dict` 만 구현한다.
    """

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def do_POST(self) -> None:  # noqa: N802  (BaseHTTPRequestHandler 규약)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                raise ApiError(400, "EMPTY_BODY", "요청 내용이 비어 있습니다.")
            if length > MAX_BODY:
                raise ApiError(413, "TOO_LARGE", "요청이 너무 큽니다.")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ApiError(400, "BAD_JSON", "요청 형식이 올바르지 않습니다.") from error
            if not isinstance(payload, dict):
                raise ApiError(400, "BAD_JSON", "요청 형식이 올바르지 않습니다.")

            self._send(200, {"ok": True, **self.run(payload)})
        except ApiError as error:
            self._send(error.status, {"ok": False, "code": error.code,
                                      "message": error.message})
        except Exception as error:  # 예상 못 한 예외도 JSON 으로 돌려준다
            fallback = api_error_from(error)
            self._send(fallback.status, {"ok": False, "code": fallback.code,
                                         "message": fallback.message})

    def do_GET(self) -> None:  # noqa: N802
        self._send(405, {"ok": False, "code": "METHOD",
                         "message": "이 주소는 POST 로만 부를 수 있습니다."})

    def log_message(self, *_args: Any) -> None:
        """액세스 로그를 끈다. 사용자가 쓴 글이 로그로 새지 않게 한다."""

    def _send(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)
