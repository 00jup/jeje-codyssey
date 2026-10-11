"""
거부불가 서버리스 함수 공통 모듈.

Vercel Python 런타임은 `api/` 안의 각 `.py` 를 독립 함수로 만든다. 밑줄로 시작하는
파일은 라우트로 만들지 않으므로, 두 엔드포인트(`compose.py` / `letter.py`)가
공유하는 코드를 여기에 둔다. 번들에 함께 실리도록 `vercel.json` 의
`includeFiles` 에도 같은 경로를 적어 둔다.

여기가 아는 것: AI 호출(Anthropic 게이트웨이) · 짧은 링크 저장소(Upstash
Redis) · 입력 검증 · 오류를 사람이 읽을 한국어로 바꾸기 · HTTP 응답.
여기가 모르는 것: 편지에 어떤 말을 쓰는지(프롬프트는 `compose.py` 에 있다).
"""

from __future__ import annotations

import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from typing import Any

# Vercel 번들에서 형제 모듈을 확실히 찾게 한다. 로컬 `dev_server.py` 와 배포 환경의
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
    """AI SDK 예외를 사람이 읽을 말로 바꾼다."""
    if isinstance(error, TimeoutError) or type(error).__name__ == "APITimeoutError":
        return ApiError(504, "TIMEOUT", "AI 응답이 늦어지고 있습니다. 잠시 후 다시 시도해 주세요.")
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
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
                    "편지를 만들지 못했습니다. 잠시 후 다시 시도해 주세요.")


# ── 입력 검증 ─────────────────────────────────────────────────────────────

def josa(word: str, with_batchim: str, without: str) -> str:
    """받침에 맞는 조사를 고른다.

    "받는 사람 이름을(를)" 같은 괄호 표기는 안내문에서 눈에 걸린다. 한글 음절은
    (코드 - 0xAC00) % 28 이 0 이 아니면 받침이 있으므로 계산으로 정해진다.
    한글이 아닌 글자로 끝나면 받침 없는 쪽을 쓴다.
    """
    if not word:
        return without
    last = word[-1]
    if "가" <= last <= "힣":
        return with_batchim if (ord(last) - 0xAC00) % 28 else without
    return without


def require_text(data: dict[str, Any], key: str, label: str, limit: int) -> str:
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


ALLOWED_STICKER_IDS = {
    "heart", "star", "sparkle", "ribbon", "crown", "flame", "cloud", "balloon",
}  # js/stickers.js 의 STICKER_ORDER 와 반드시 같아야 한다 — 그림은 거기 있고 여긴 이름만 검증한다

MAX_DECORATIONS = 6
MAX_PHOTO_DECORATIONS = 2
MAX_PHOTO_DATA_URI_LEN = 700_000  # 클라이언트가 640px/JPEG로 줄인 뒤 넉넉히 잡은 상한


def sanitize_decorations(raw: Any) -> list[dict[str, Any]]:
    """편지지 꾸밈(스티커·사진) 배열을 검증하고 안전한 값만 남긴다.

    스티커는 화이트리스트에 없으면 그 항목만 조용히 버린다 — 정상 UI에서는
    나올 수 없는 값이라 사용자 잘못이 아니다. 사진이 너무 크거나 너무 많으면
    사용자가 뭘 했는지 알 수 있는 상황이라 명확히 오류로 알린다.
    """
    if not isinstance(raw, list):
        return []

    out: list[dict[str, Any]] = []
    photo_count = 0
    for item in raw[:MAX_DECORATIONS]:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        src = str(item.get("src") or "")

        if kind == "sticker":
            if src not in ALLOWED_STICKER_IDS:
                continue
        elif kind == "photo":
            if not src.startswith("data:image/"):
                continue
            if len(src) > MAX_PHOTO_DATA_URI_LEN:
                raise ApiError(400, "PHOTO_TOO_LARGE",
                               "사진이 너무 큽니다. 다른 사진으로 다시 시도해 주세요.")
            photo_count += 1
            if photo_count > MAX_PHOTO_DECORATIONS:
                raise ApiError(400, "TOO_MANY_PHOTOS",
                               f"사진은 최대 {MAX_PHOTO_DECORATIONS}장까지 넣을 수 있습니다.")
        else:
            continue

        def clamp(value: Any, lo: float, hi: float, default: float) -> float:
            try:
                return max(lo, min(hi, float(value)))
            except (TypeError, ValueError):
                return default

        out.append({
            "kind": kind,
            "src": src,
            "x": clamp(item.get("x"), 0, 100, 50),
            "y": clamp(item.get("y"), 0, 100, 50),
            "scale": clamp(item.get("scale"), 0.3, 3, 1),
            "rotation": clamp(item.get("rotation"), -45, 45, 0),
        })
    return out


def pick(data: dict[str, Any], key: str, allowed: dict[str, str], default: str) -> str:
    """선택지 값을 화이트리스트로 거른다.

    이 값들은 프롬프트 문장에 그대로 들어간다. 걸러내지 않으면 select 를 조작해
    임의 문장을 프롬프트에 심을 수 있다.
    """
    value = str(data.get(key) or "").strip()
    return value if value in allowed else default


# ── AI: Claude ────────────────────────────────────────────────────────────
# Codyssey 과정용 Anthropic 호환 게이트웨이를 사용한다.
COPA_ANTHROPIC_BASE = "https://copa.codyssey.kr"
ANTHROPIC_MODEL = "claude-haiku-4"


def _extract_json_object(text: str) -> dict[str, Any]:
    """모델이 설명을 덧붙여도 본문의 JSON 객체만 뽑아낸다."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("응답에서 JSON 객체를 찾지 못했다")
    return json.loads(match.group(0))


def anthropic_json(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Anthropic 호환 엔드포인트로 JSON 을 받는다.

    과정용 게이트웨이에 프롬프트로 스키마를 전달하고 "JSON만 출력하라"고
    요청한 뒤 텍스트에서 JSON 객체를 뽑는다. 형식이 어긋나면 한 번만 다시 시킨다.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ApiError(500, "NO_KEY", "서버에 ANTHROPIC_API_KEY 가 설정되지 않았습니다.")

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key, base_url=COPA_ANTHROPIC_BASE,
                       timeout=10, max_retries=0)
    schema_hint = json.dumps(schema, ensure_ascii=False)

    last: Exception | None = None
    for attempt in range(2):
        nudge = "" if attempt == 0 else "\n\n방금 응답이 JSON 형식을 어겼다. 설명 없이 JSON 객체 하나만 출력하라."
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1536,
                messages=[{
                    "role": "user",
                    "content": (
                        prompt + nudge +
                        f"\n\n반드시 이 JSON 스키마를 만족하는 객체 하나만 출력한다. "
                        f"설명, 코드블록, 머리말을 붙이지 않는다:\n{schema_hint}"
                    ),
                }],
            )
        except Exception as error:
            raise api_error_from(error) from error

        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            last = ApiError(502, "EMPTY", "AI가 빈 응답을 돌려줬습니다.")
            continue
        try:
            return _extract_json_object(text)
        except (ValueError, json.JSONDecodeError) as error:
            last = error

    raise ApiError(502, "BAD_SHAPE",
                   "AI 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.") from last


def ai_json(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Claude로 편지 JSON을 생성한다."""
    return anthropic_json(prompt, schema)


# ── 저장소: Upstash Redis (REST) ────────────────────────────────────────────
#
# Vercel 함수는 요청마다 새로 뜨는 상태 없는 프로세스라 파일이나 메모리에 저장할
# 수 없다. Upstash 는 HTTP 로 Redis 명령을 보내는 REST API 를 주므로, 별도
# 클라이언트 라이브러리 없이 표준 라이브러리 `urllib` 만으로 쓴다.

LETTER_TTL_SECONDS = 30 * 24 * 60 * 60  # 30일 — 장난 편지가 무한히 쌓이지 않게
ID_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"  # 0/O/1/l/I 처럼 헷갈리는 글자는 뺐다
ID_LENGTH = 5  # 무작위로 만들 때의 길이 — 직접 정하는 주소는 길이가 다르다

# 짧은 링크는 무작위(ID_ALPHABET, 5자)로 만들거나, 보내는 사람이 직접 정한 문구를
# 쓴다(3~20자, 하이픈 허용, 앞뒤는 영문·숫자). 둘 다 이 패턴 하나로 받는다 —
# read.html·letter.py 양쪽이 조회 전에 형식을 먼저 확인하는 데 쓴다.
SHORT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,18}[a-z0-9]$")

RESERVED_IDS = {"api", "css", "js", "images", "docs", "screenshots", "read", "index", "favicon"}


def sanitize_custom_id(raw: str) -> str:
    """사람이 입력한 주소 후보를 URL에 쓸 수 있는 꼴로 다듬는다.

    소문자·숫자·하이픈만 남기고, 나머지(공백·한글·특수문자)는 하이픈으로
    바꾼다. 연속 하이픈은 하나로 줄이고, 앞뒤 하이픈은 잘라낸다.
    """
    slug = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:20]


def _redis_command(*args: str) -> Any:
    url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip()
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if not url or not token:
        raise ApiError(500, "NO_KV",
                       "서버에 저장소(UPSTASH_REDIS_REST_URL/TOKEN)가 설정되지 않았습니다.")

    body = json.dumps(list(args)).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/"), data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise ApiError(502, "KV_ERROR", "저장소에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.") from error
    if "error" in payload:
        raise ApiError(502, "KV_ERROR", "저장소 요청이 실패했습니다.")
    return payload.get("result")


def kv_get(key: str) -> dict[str, Any] | None:
    raw = _redis_command("GET", key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def kv_set_if_new(key: str, value: dict[str, Any], ttl: int) -> bool:
    """키가 없을 때만 저장한다(`NX`). 이미 있으면 False — 짧은 ID 충돌(또는 이미
    쓰이고 있는 커스텀 주소)을 뜻한다."""
    raw = json.dumps(value, ensure_ascii=False)
    result = _redis_command("SET", key, raw, "NX", "EX", str(ttl))
    return result == "OK"


_HANGUL_INITIALS = [
    "g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s",
    "ss", "", "j", "jj", "ch", "k", "t", "p", "h",
]
_HANGUL_MEDIALS = [
    "a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa",
    "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i",
]
_HANGUL_FINALS = [
    "", "k", "k", "k", "n", "n", "n", "t", "l", "k",
    "m", "l", "l", "l", "p", "l", "m", "p", "p", "t",
    "t", "ng", "t", "t", "k", "t", "p", "t",
]


def romanize_ko(text: str) -> str:
    """한글을 로마자로 바꾼다(국어의 로마자 표기법, 간략 버전).

    링크 이름을 이름에서 만들 때 쓴다 — "하은" 같은 한글 이름도 사람이 읽고
    타이핑할 수 있는 주소("haeun")가 되게 하려는 것이라, 표준 표기법의 예외
    규칙(음운 변화 등)까지는 재현하지 않는다. 글자 하나하나를 초성·중성·종성으로
    풀어 이어 붙이는 정도로 충분하다.
    """
    out: list[str] = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code <= 11171:
            initial, rem = divmod(code, 21 * 28)
            medial, final = divmod(rem, 28)
            out.append(_HANGUL_INITIALS[initial] + _HANGUL_MEDIALS[medial] + _HANGUL_FINALS[final])
        elif ch.isascii() and ch.isalnum():
            out.append(ch.lower())
        # 그 밖(공백·특수문자·한자 등)은 링크에 못 쓰니 그냥 버린다.
    return "".join(out)


def build_name_slug(sender: str, receiver: str) -> str:
    """보내는 사람·받는 사람 이름으로 링크 기본값을 만든다.

    각 이름을 7자로 잘라 둔다 — 안 그러면 충돌 시 붙이는 접미사(`-xyz`)까지
    합쳐 20자 한도를 넘길 수 있다.
    """
    parts = [sanitize_custom_id(romanize_ko(name))[:7] for name in (sender, receiver)]
    return "-".join(p for p in parts if p)


def new_named_id(value: dict[str, Any], base: str) -> str:
    """이름 기반 기본 슬러그로 먼저 시도하고, 겹치면 짧은 접미사를 붙여 재시도한다.

    둘 다 실패하면(아주 흔한 이름이 계속 겹치는 경우) 완전 무작위로 물러난다 —
    사용자가 링크를 못 받는 것보다는 무작위 링크라도 받는 게 낫다.
    """
    if base and len(base) >= 3 and base not in RESERVED_IDS:
        if kv_set_if_new(f"letter:{base}", value, LETTER_TTL_SECONDS):
            return base
        for _ in range(4):
            suffix = "".join(secrets.choice(ID_ALPHABET) for _ in range(3))
            candidate = f"{base}-{suffix}"
            if kv_set_if_new(f"letter:{candidate}", value, LETTER_TTL_SECONDS):
                return candidate
    return new_short_id(value)


def new_short_id(value: dict[str, Any]) -> str:
    """충돌하지 않는 짧은 ID 를 만들어 값을 저장하고 그 ID 를 돌려준다."""
    for _ in range(5):
        candidate = "".join(secrets.choice(ID_ALPHABET) for _ in range(ID_LENGTH))
        if kv_set_if_new(f"letter:{candidate}", value, LETTER_TTL_SECONDS):
            return candidate
    raise ApiError(500, "ID_COLLISION", "링크를 만들지 못했습니다. 다시 시도해 주세요.")


# ── HTTP ──────────────────────────────────────────────────────────────────

# Two compressed photos may each contain up to 700,000 characters.
MAX_BODY = 2 * 1024 * 1024


class BaseHandler(BaseHTTPRequestHandler):
    """POST/GET JSON 핸들러의 공통 부분.

    하위 클래스는 필요한 쪽만 구현한다 — POST 만 받으면 `run()`, GET 만 받으면
    `run_query()`. 구현하지 않은 쪽은 자동으로 405 를 준다.
    """

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def run_query(self, params: dict[str, list[str]]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def do_POST(self) -> None:  # noqa: N802
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
        except NotImplementedError:
            self._send(405, {"ok": False, "code": "METHOD",
                             "message": "이 주소는 GET 으로만 부를 수 있습니다."})
        except ApiError as error:
            self._send(error.status, {"ok": False, "code": error.code, "message": error.message})
        except Exception as error:
            fallback = api_error_from(error)
            self._send(fallback.status, {"ok": False, "code": fallback.code,
                                         "message": fallback.message})

    def do_GET(self) -> None:  # noqa: N802
        try:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            self._send(200, {"ok": True, **self.run_query(query)})
        except NotImplementedError:
            self._send(405, {"ok": False, "code": "METHOD",
                             "message": "이 주소는 POST 로만 부를 수 있습니다."})
        except ApiError as error:
            self._send(error.status, {"ok": False, "code": error.code, "message": error.message})
        except Exception as error:
            fallback = api_error_from(error)
            self._send(fallback.status, {"ok": False, "code": fallback.code,
                                         "message": fallback.message})

    def log_message(self, *_args: Any) -> None:
        """액세스 로그를 끈다. 사용자가 쓴 내용이 로그로 새지 않게 한다."""

    def _send(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)
