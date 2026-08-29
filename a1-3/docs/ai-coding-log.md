# AI 코딩 도구 사용 기록

도구: **Claude Code (Opus 5)** · 작업일 2026-08-30 · 작업 시간 약 1시간

대화 화면 캡처는 [`../screenshots/ai-tool/`](../screenshots/ai-tool/) 에 넣는다.
이 문서는 그 캡처가 무엇을 보여주는지, 그리고 **AI가 준 코드를 그대로 쓰지 않고
어디를 고쳤는지**를 적는다.

---

## 1. 무엇을 시켰나

기존 사내 대시보드(`jejelabs-metrics`, Cloudflare Worker + TypeScript)에 있던
"AI 리뷰 답글 초안" 기능의 **프롬프트 설계 원칙만** 가져와, 과제 요구 스택
(바닐라 프론트 + Vercel Python 서버리스 + AI API)으로 새로 만들라고 지시했다.

가져온 원칙은 셋이다.

| 원칙 | 원본에서 배운 이유 |
| --- | --- |
| 답글은 **댓글의 언어**로 쓴다 | 한국 스토어에 영어로 남긴 리뷰에 한국어 답글이 나간 사고가 있었다 |
| **없는 기능을 인정하지 않는다** | 동조하려고 사실을 양보하면 그 답글이 공개로 남는다 |
| **초안까지만** 만든다 | 자동 게시는 되돌릴 수 없다 |

코드는 한 줄도 복사하지 않았다. TypeScript/Cloudflare 구조는 이 과제의 제약
(Python/Vercel)과 맞지 않고, 원본 저장소는 비공개다.

---

## 2. AI가 낸 것을 그대로 쓰지 않은 지점

이 절이 이 문서의 핵심이다. "시키는 대로"가 아니라 **왜 고쳤는지**를 남긴다.

### 2-1. `api/_shared.py` 를 두 함수가 import 하지 못하는 문제

첫 코드는 `from _shared import ...` 만 있었다. 로컬에서는 잘 돌지만
**배포하면 `ModuleNotFoundError` 가 난다** — Vercel은 각 `.py` 를 따로 번들하고,
번들에 안 실린 파일은 존재하지 않는다.

고친 것 두 가지:

```python
# api/_shared.py — 배포 환경의 작업 디렉터리가 달라서 경로를 직접 잡아준다
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

```jsonc
// vercel.json — 번들에 _shared.py 를 같이 싣는다
"functions": { "api/draft.py": { "includeFiles": "api/_shared.py" } }
```

**배운 것:** 로컬에서 되는 것이 배포에서 되는 것과 같지 않다. 특히 파일 경로와
환경 변수는 두 환경이 다른 방식으로 주입한다.

### 2-2. 로컬 개발 서버가 응답을 안 하고 멈춘 문제

`dev_server.py` 의 첫 버전은 API 요청을 이렇게 넘겼다.

```python
route.do_POST(self)      # ← 여기가 틀렸다
```

`self` 는 개발 서버의 핸들러라서 `_shared.JsonHandler` 가 쓰는 `self.run()` 과
`self._send()` 를 갖고 있지 않다. 그렇다고 `route(...)` 로 정상 생성하면
`BaseHTTPRequestHandler.__init__` 이 **생성되는 순간 요청을 다시 파싱하고 통신까지
해버려서** 같은 연결을 두 번 잡는다.

`__init__` 없이 만들고 소켓·헤더만 빌려주는 쪽으로 바꿨다.

```python
proxy = route.__new__(route)          # __init__ 을 부르지 않는다
proxy.headers, proxy.rfile, proxy.wfile = self.headers, self.rfile, self.wfile
proxy.send_response = self.send_response
proxy.end_headers = super().end_headers   # 중복 헤더를 피한다
getattr(proxy, method)()
```

**배운 것:** 오류 메시지 없이 "그냥 멈추는" 증상은 대개 소켓을 두 곳에서 잡을 때다.
스택 트레이스가 안 나온다고 원인이 없는 게 아니다.

### 2-3. `"오늘 할 이야기을(를) 입력해 주세요"`

AI가 낸 안내문은 조사를 괄호로 처리했다. 실제 화면에서 눈에 걸려 계산으로 바꿨다.

```python
def josa(word, with_batchim, without):
    last = word[-1]
    if "가" <= last <= "힣":
        return with_batchim if (ord(last) - 0xAC00) % 28 else without
    return without
```

→ "받은 댓글**을**", "오늘 할 이야기**를**"

### 2-4. 모델이 500자를 넘긴 조각을 낼 때

프롬프트에 "500자를 넘기지 마라"고 적어도 가끔 넘는다. 그대로 내보내면 사용자가
붙여넣는 순간 Threads가 게시를 거부한다. 서버에서 한 번 더 자르게 했다.

```python
pieces = [p[:THREADS_LIMIT] for p in pieces][:5]
```

**배운 것:** 프롬프트는 지시이고 코드는 보장이다. 지켜야 하는 규칙은 코드에도 둔다.

### 2-5. `<select>` 값을 프롬프트에 그대로 넣던 코드

말투·조각 수 값이 프롬프트 문장에 직접 들어가고 있었다. 브라우저에서 `<select>`
값을 바꾸면 임의 문장을 프롬프트에 심을 수 있다. 서버에서 화이트리스트로 거르게
바꿨다.

```python
def pick(data, key, allowed, default):
    return allowed.get(str(data.get(key) or "").strip(), allowed[default])
```

### 2-6. 반응형이 깨진 줄 알았던 건

헤드리스 브라우저로 390px 스크린샷을 찍었더니 화면이 잘려 보여서 레이아웃이
깨진 줄 알았다. 실제로 재보니 **헤드리스 크롬이 뷰포트를 485px 아래로 못 줄이는**
것이었고, 레이아웃은 멀쩡했다.

```js
document.documentElement.scrollWidth === document.documentElement.clientWidth  // true
```

**배운 것:** 스크린샷은 증상이지 원인이 아니다. 숫자로 재기 전에는 고치지 않는다.

---

## 3. 검증 순서

AI가 짠 코드를 믿지 않고 순서대로 확인했다.

1. `python3 -c "import ast; ast.parse(...)"` — 문법
2. `node --check js/app.js` — 프론트 문법
3. `curl` 로 엔드포인트 6가지 경우 확인 (정상 / 빈 값 / 초과 / 잘못된 JSON / GET / 영어 댓글)
4. 헤드리스 크롬으로 400·768·1440px에서 `scrollWidth === clientWidth` 측정
5. 다크 모드에서 실제 AI 호출까지 돌려 화면 확인

3번의 마지막(영어 댓글 → 영어 답글)이 이 서비스의 핵심 검증이다.
결과는 [`../README.md#7-테스트-기록`](../README.md) 에 있다.

---

## 4. 캡처에 담을 것

`screenshots/ai-tool/` 에 넣을 대화 화면은 아래를 포함하면 좋다.

| 파일 | 내용 |
| --- | --- |
| `01-requirements.png` | 무엇을 만들지 지시한 첫 대화 |
| `02-api-implementation.png` | 서버리스 함수 코드를 만들어 가는 과정 |
| `03-debugging.png` | 위 2-1 또는 2-2의 오류를 잡는 과정 |
| `04-verification.png` | `curl` 로 엔드포인트를 검증하는 화면 |

키가 화면에 보이지 않는지 확인하고 올린다. `.env` 파일 내용이나 터미널의
환경 변수 출력이 찍히지 않게 한다.
