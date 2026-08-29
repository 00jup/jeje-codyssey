# a1-3: 타래공방 — Threads 타래·답글 초안 웹 서비스

소재 한 줄을 넣으면 Threads(스레드)에 올릴 **타래 초안**이 나오고, 받은 댓글을
붙여 넣으면 **답글 초안 두 벌**이 나오는 웹 서비스다. 프론트엔드는 순수
HTML/CSS/JavaScript, 백엔드는 Vercel Serverless Functions(Python), AI는 Google
Gemini API를 쓴다.

**초안까지만 만든다.** 자동 게시가 없다 — 맥락을 놓친 답글이 공개로 남는 것은
답을 달지 않은 것보다 나쁘기 때문이다.

- 배포 URL: <!-- 배포 후 채운다 --> `https://tarae-gongbang.vercel.app`
- 저장소: https://github.com/00jup/jeje-codyssey (`a1-3/`)
- 서비스 기획서: [`docs/서비스기획서.md`](./docs/서비스기획서.md)
- AI 코딩 도구 사용 기록: [`docs/ai-coding-log.md`](./docs/ai-coding-log.md)

---

## 1. 제출 요구사항 대응

| 요구사항 | 어떻게 만족했나 | 확인 위치 |
| --- | --- | --- |
| 3개 이상 페이지/섹션 + 메뉴 이동 | 홈 · 타래 짓기 · 답글 짓기 · 사용법 · 소개 **5개**. 해시 라우팅으로 한 번에 한 화면만 보인다 | [`js/app.js` 라우팅](./js/app.js) · [`index.html`](./index.html) |
| 반응형 | 860px에서 햄버거 메뉴로, 560px에서 1열로 전환. 실측으로 가로 스크롤 0 확인 | [`css/style.css` 반응형](./css/style.css) · [검증 방법](#5-반응형-검증) |
| AI API 연동 기능 1개 이상 | **2개** — 타래 초안 생성, 답글 초안 생성 | [`api/draft.py`](./api/draft.py) · [`api/reply.py`](./api/reply.py) |
| 프론트/백엔드 구조 분리 | `index.html` · `css/` · `js/` 와 `api/` 가 갈려 있고, 프론트는 API 키를 모른다 | [프로젝트 구조](#3-프로젝트-구조) |
| 실패 처리 | 빈 입력 · API 오류(4xx/5xx) · 타임아웃 **셋 다** 안내 문구로 처리 | [실패 처리](#6-실패-처리-기준) |
| requirements.txt | `google-genai` | [`requirements.txt`](./requirements.txt) |
| 환경 변수로 키 관리 | 키는 서버리스 함수의 `os.environ` 에서만 읽는다. 프론트 코드·저장소·스크린샷 어디에도 없다 | [환경 변수](#4-환경-변수-설정) |
| 보너스 — UX 고도화 | 다크 모드(자동/라이트/다크 3단 토글, localStorage 기억), 로딩 스켈레톤, 복사 토스트, 글자 수 카운터 | [`css/style.css`](./css/style.css) · [`js/app.js`](./js/app.js) |

---

## 2. 기술 스택

| 층 | 사용 기술 | 고른 이유 |
| --- | --- | --- |
| 프론트엔드 | HTML5 · CSS3 · JavaScript (ES5 문법, 프레임워크·빌드 도구 없음) | 과제 제약. 빌드가 없으니 저장소의 파일이 곧 배포되는 파일이다 |
| 라우팅 | `location.hash` + `history.pushState` | 주소 하나가 곧 화면 하나여서 그대로 공유된다 |
| 백엔드 | Vercel Serverless Functions (Python 3.12) | 상시 서버 없이 요청이 올 때만 뜬다. API 키를 브라우저에 내리지 않기 위한 최소한의 서버다 |
| AI | Google Gemini API (`gemini-3.7-flash`) — 구조화 JSON 출력 | b2-2·a2-1에서 쓰던 키를 그대로 쓴다. JSON 스키마를 강제할 수 있어 파싱이 무너지지 않는다 |
| HTTP | Python 표준 라이브러리 `BaseHTTPRequestHandler` | Flask/FastAPI 없이 Vercel 규약을 그대로 따른다. 콜드 스타트가 짧다 |
| 배포 | GitHub → Vercel 자동 배포 | `main` 에 푸시하면 배포된다 |

---

## 3. 프로젝트 구조

```
a1-3/
├── index.html            # 5개 섹션이 한 문서에 있고, JS가 하나씩만 보여준다
├── css/
│   └── style.css         # 토큰 → 레이아웃 → 컴포넌트 → 반응형
├── js/
│   └── app.js            # 라우팅 · 테마 · 폼 → fetch → 렌더 · 복사
├── images/
│   └── favicon.svg
├── api/                  # ← 백엔드. Vercel이 각 .py를 함수 하나로 만든다
│   ├── _shared.py        # 공통: Gemini 호출 · 입력 검증 · 오류 번역 · HTTP 응답
│   ├── draft.py          # POST /api/draft  — 타래 초안
│   └── reply.py          # POST /api/reply  — 답글 초안
├── dev_server.py         # 로컬 개발 서버(표준 라이브러리만 사용)
├── requirements.txt
├── vercel.json           # 함수 메모리·타임아웃·보안 헤더
├── .env.example
├── docs/
│   ├── 서비스기획서.md
│   └── ai-coding-log.md
└── screenshots/          # 제출용 증빙 (아래 8절 참고)
```

`api/_shared.py` 는 밑줄로 시작해서 Vercel이 라우트로 만들지 않는다. 두 함수가
공유하도록 `vercel.json` 의 `includeFiles` 에 같이 실어 보낸다.

### 요청이 흐르는 길

```
사용자 입력
   └─ [브라우저] app.js  submit 가로채기 → 빈 값 검사
        └─ fetch('/api/draft', {method:'POST', body: JSON})   ← 25초 타임아웃
             └─ [Vercel] api/draft.py  handler.do_POST
                  └─ 입력 검증 → 프롬프트 조립 → Gemini 호출(JSON 스키마 강제)
                       └─ 500자 초과분 잘라내기
                  └─ {"ok":true, "pieces":[...]}  또는  {"ok":false,"message":"..."}
        └─ [브라우저] 조각 카드로 그리기 / 실패면 안내 문구
```

**API 키는 이 그림에서 오른쪽 절반에만 있다.** 브라우저는 키를 본 적이 없다.

---

## 4. 환경 변수 설정

필요한 값은 하나다.

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `GEMINI_API_KEY` | ✅ | [Google AI Studio](https://aistudio.google.com/apikey)에서 발급 |
| `GEMINI_MODEL` | — | 비우면 `gemini-3.7-flash` |

### 로컬

```bash
cd a1-3
cp .env.example .env
# .env 를 열어 GEMINI_API_KEY 값을 채운다
```

`.env` 는 [`.gitignore`](./.gitignore)에 있어 커밋되지 않는다. `dev_server.py` 가
이 파일을 읽어 `os.environ` 에 넣는다.

### 배포 (Vercel)

Vercel 대시보드 → 프로젝트 → **Settings → Environment Variables** 에서
`GEMINI_API_KEY` 를 Production·Preview·Development 모두에 추가한다. 추가한 뒤에는
**재배포해야 반영된다**(Deployments → 최신 배포 → Redeploy).

`.env` 파일은 배포에 올라가지 않는다. 로컬은 `.env`, 배포는 대시보드 — 같은 이름의
환경 변수를 서로 다른 곳에서 주입하는 것이 이 구조의 핵심이다.

> **키가 노출됐다면** 즉시 Google AI Studio에서 해당 키를 삭제하고 새로 발급한 뒤,
> Vercel 환경 변수를 교체하고 재배포한다. 커밋에 섞여 들어갔다면 키 폐기가 먼저다 —
> 히스토리를 지워도 이미 공개된 값은 되돌릴 수 없다.

---

## 5. 실행 방법

### 로컬 실행

```bash
cd a1-3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 dev_server.py            # → http://localhost:3000
```

`dev_server.py` 는 정적 파일을 서빙하면서 `/api/draft`, `/api/reply` 를 **배포와 같은
핸들러 클래스**로 넘긴다. 프론트엔드 코드는 로컬과 배포에서 한 줄도 다르지 않다.

Vercel CLI가 있으면 그쪽이 배포 환경에 더 가깝다:

```bash
npm i -g vercel
vercel dev
```

### 반응형 검증

브라우저 개발자 도구의 디바이스 툴바로 **iPhone 폭(390px)** 과 **데스크톱(1440px)**
두 가지에서 확인했다. 자동 검증은 다음 한 줄로 한다 — 가로 스크롤이 생기면
`scrollWidth` 가 `clientWidth` 보다 커진다.

```js
// 콘솔에 붙여 넣는다. true 면 가로 스크롤 없음
document.documentElement.scrollWidth === document.documentElement.clientWidth
```

| 폭 | 바뀌는 것 |
| --- | --- |
| ~860px 이하 | 상단 메뉴 → 햄버거 메뉴 |
| ~560px 이하 | 말투·조각 수 2열 → 1열, 여백 축소, 본문 15.5px |

### 배포

1. 이 저장소를 Vercel에 임포트한다.
2. **Root Directory** 를 `a1-3` 로 지정한다. (저장소 루트가 아니다)
3. Framework Preset: **Other**. 빌드 명령은 비워 둔다.
4. Environment Variables에 `GEMINI_API_KEY` 를 넣는다.
5. Deploy. 이후 `main` 브랜치에 푸시하면 자동 재배포된다.

---

## 6. 실패 처리 기준

과제 요구는 "최소 1개"지만 셋 다 넣었다. 화면에 뜨는 문장은 모두 **서버가 정한
문장**이다 — 프론트가 상태 코드만 보고 문구를 지어내면 같은 말을 두 군데서 관리하게 된다.

| 상황 | 어디서 막나 | 사용자가 보는 것 |
| --- | --- | --- |
| 빈 입력 | 브라우저 (`js/app.js`) — 서버까지 가지 않는다 | "답할 댓글을 붙여 넣어 주세요." + 입력칸 빨간 테두리 + 포커스 이동 |
| 입력 초과 (1200자) | 서버 (`_shared.require_text`) | "오늘 할 이야기는 1200자까지 넣을 수 있습니다. 지금 1300자입니다." |
| 인증 실패 (401/403) | 서버 (`_shared.api_error_from`) | "AI 서버 인증에 실패했습니다. 관리자에게 알려주세요." |
| 호출 한도 (429) | 서버 | "지금 요청이 몰렸습니다. 30초쯤 뒤에 다시 시도해 주세요." |
| 업스트림 5xx | 서버 | "AI 서버가 응답하지 못했습니다. 잠시 후 다시 시도해 주세요." |
| 응답 지연 | 브라우저 `AbortController` 25초 | "응답이 25초를 넘겼습니다. 소재를 조금 줄이거나 잠시 후 다시 시도해 주세요." |
| 네트워크 끊김 | 브라우저 `fetch` reject | "네트워크에 연결하지 못했습니다. 연결 상태를 확인해 주세요." |
| AI가 형식을 어김 | 서버 — 1회 재시도 후 실패 처리 | "AI 응답 형식이 올바르지 않습니다. 다시 시도해 주세요." |

---

## 7. 테스트 기록

로컬 서버(`python3 dev_server.py`)에 직접 요청해 확인한 결과다.

```bash
# 1) 정상 입력 — 타래 3조각 + 해시태그
curl -s -X POST http://localhost:3000/api/draft \
  -H 'Content-Type: application/json' \
  -d '{"topic":"사진 정리 앱을 3개월째 혼자 만들고 있다. 이번 주에 중복 사진 찾는 기능을 넣었는데, 2만 장 도는 데 40초 걸리던 게 4초로 줄었다.","tone":"회고","count":"3","hashtags":true}'
# → 200 {"ok":true,"pieces":[…3개…],"hashtags":["#개발일지","#1인개발","#앱개발"], …}

# 2) 빈 입력
curl -s -X POST http://localhost:3000/api/reply \
  -H 'Content-Type: application/json' -d '{"comment":""}'
# → 400 {"ok":false,"code":"EMPTY_INPUT","message":"받은 댓글을 입력해 주세요."}

# 3) 긴 입력 (1300자)
# → 400 {"ok":false,"code":"TOO_LONG","message":"오늘 할 이야기는 1200자까지 넣을 수 있습니다. 지금 1300자입니다."}

# 4) 잘못된 JSON
curl -s -X POST http://localhost:3000/api/reply -d 'not json'
# → 400 {"ok":false,"code":"BAD_JSON","message":"요청 형식이 올바르지 않습니다."}

# 5) GET 으로 호출
curl -s http://localhost:3000/api/draft
# → 405 {"ok":false,"code":"METHOD","message":"이 주소는 POST 로만 부를 수 있습니다."}

# 6) 영어 댓글 → 영어 답글 (원글은 한국어)
curl -s -X POST http://localhost:3000/api/reply \
  -H 'Content-Type: application/json' \
  -d '{"post":"사진 정리 앱에 중복 사진 찾기를 넣었다.","comment":"Does this work on Android? I dont have an iPhone :(","intent":"안드로이드는 계획에 없다고 솔직하게. 대신 웹 버전 준비 중이라고 안내"}'
# → 200 {"kind":"질문","language":"English",
#        "short":"Currently, there are no plans for an Android app, but we are working on a web version.", …}
```

6번이 이 서비스의 핵심 검증이다. **원글이 한국어여도 댓글이 영어면 영어로 답한다** —
스토어 국가나 원글 언어가 아니라 댓글에 쓰인 글자를 본다.

---

## 8. 스크린샷 넣는 위치

빈 폴더를 만들어 뒀다. 아래 파일 이름 그대로 넣으면 이 문서의 링크가 살아난다.

| 폴더 | 파일 이름 | 무엇을 찍나 |
| --- | --- | --- |
| `screenshots/desktop/` | `01-home.png` | 데스크톱 홈 화면 (1440px 정도) |
| | `02-draft-result.png` | **AI 타래 초안이 나온 화면** (입력 + 결과가 같이 보이게) |
| | `03-reply-result.png` | **AI 답글 초안이 나온 화면** |
| | `04-error.png` | 실패 처리 화면 (빈 입력 안내 문구가 뜬 상태) |
| | `05-dark.png` | 다크 모드 (보너스 증빙) |
| `screenshots/mobile/` | `01-home.png` | 모바일 홈 (390px 정도 또는 실제 폰) |
| | `02-menu.png` | 햄버거 메뉴를 연 상태 |
| | `03-draft-result.png` | 모바일에서 AI 결과가 나온 화면 |
| `screenshots/ai-tool/` | `01-*.png` … | AI 코딩 도구 대화 화면 캡처 |

자세한 촬영 순서는 [`screenshots/README.md`](./screenshots/README.md) 에 적어 뒀다.

배포 URL을 받은 뒤에는 이 문서 맨 위의 `배포 URL` 줄과
[`docs/서비스기획서.md`](./docs/서비스기획서.md) 의 같은 줄을 함께 채운다.

---

## 9. 만들면서 짚은 것

**API 키를 왜 프론트에 두면 안 되나.** `js/app.js` 에 키를 적으면 브라우저 개발자
도구의 Sources 탭에서 그대로 읽힌다. 난독화도 소용없다 — 실행되려면 결국 평문이
되어야 한다. 그래서 키를 아는 코드는 서버리스 함수 안에만 두고, 브라우저는
`/api/...` 라는 우리 주소만 안다. 키가 새면 남의 요금이 우리 쿼터로 나간다.

**로컬과 배포는 무엇이 다른가.** 로컬은 `dev_server.py` 한 프로세스가 정적 파일과
API를 같이 처리하고 `.env` 를 읽는다. 배포에서는 정적 파일을 CDN이, API를 함수가
따로 맡고 환경 변수는 Vercel이 주입한다. 그래서 `.env` 를 배포에 올리려 하면 안 되고,
반대로 대시보드에만 키를 넣고 로컬에서 돌리면 500이 난다. **양쪽에 각각 넣어야 한다.**

**Vercel Python 함수에서 형제 모듈 import.** `api/draft.py` 가 `api/_shared.py` 를
import 하려면 두 가지가 필요하다 — `vercel.json` 의 `includeFiles` 로 번들에 같이
싣고, `sys.path` 에 `api/` 디렉터리를 넣는 것이다. 로컬에서는 작업 디렉터리가 달라서
둘 없이도 되는데 배포하면 `ModuleNotFoundError` 가 난다. 로컬에서 되니까 됐다고
넘기면 배포 후에 처음 알게 되는 종류의 실패다.

**모델이 500자를 넘길 때.** 프롬프트에 "500자를 넘기지 마라"고 적어도 가끔 넘는다.
그대로 화면에 내보내면 사용자가 붙여넣는 순간 게시가 막힌다. 그래서 서버에서 한 번
더 자른다 — 프롬프트는 지시이고 코드는 보장이다.

**한국어 조사.** `f"{label}을(를) 입력해 주세요"` 는 안내문에서 눈에 걸린다.
한글 음절은 `(코드 - 0xAC00) % 28` 이 0이 아니면 받침이 있으므로,
`_shared.josa()` 가 "받은 댓글**을**", "오늘 할 이야기**를**" 를 계산해서 고른다.
