# 거부불가 — 여자친구에게 보내는 AI 여행 초대 편지

여행 장소와 전하고 싶은 말을 적으면 Claude가 초대 편지와 장난스러운 대사를
만듭니다. 스티커·사진으로 꾸민 뒤 링크를 공유하면, 받는 사람은 도망가는
거부 버튼과 수락 버튼이 있는 화면에서 편지를 열어볼 수 있습니다.

- 서비스: [https://geobulga.vercel.app](https://geobulga.vercel.app)
- GitHub: [00jup/jeje-codyssey](https://github.com/00jup/jeje-codyssey/tree/main/a1-3)
- [서비스 기획서](docs/서비스기획서.md)
- [배포 검증 기록](docs/배포검증.md)
- [AI 코딩 도구 사용 기록](docs/ai-coding-log.md) · [실제 이번 작업 대화 발췌](docs/2026-10-11-codex-log.md)
- [스크린샷 안내](screenshots/README.md)

## 기술 스택과 구조

프론트엔드는 순수 HTML/CSS/JavaScript이며 React/Vue나 빌드 도구를 사용하지 않습니다.
백엔드는 Vercel Python 3.12 Serverless Functions입니다. Claude는 Codyssey의
Anthropic 호환 게이트웨이로 호출합니다. 편지는 Upstash Redis에 30일간 저장합니다.

```text
a1-3/
├── index.html               # 홈 / 편지 만들기 / 사용법 / 소개
├── read.html                # 공유 링크를 받은 사람이 여는 화면
├── css/                     # 반응형 스타일 / 편지 공개 화면 스타일
├── js/                      # 메뉴, fetch, 결과 렌더링, 스티커, 버튼 장난
├── images/favicon.svg
├── api/
│   ├── compose.py           # POST /api/compose: Claude 생성 + Redis 저장
│   ├── letter.py            # GET /api/letter?id=...: 저장된 편지 조회
│   └── _shared.py           # AI 호출, 입력 검증, Redis, JSON 응답
├── dev_server.py            # 로컬 정적 파일/API 서버
├── requirements.txt         # anthropic SDK
├── .env.example             # 환경 변수 이름과 예시 값만 포함
├── .python-version          # Vercel Python 3.12 지정
├── .vercelignore            # 환경 파일·가상환경·증빙을 배포에서 제외
├── vercel.json              # Python 함수 / 공유 링크 rewrite / 보안 헤더
├── docs/                    # 기획서, 대화 기록, 검증 기록
└── screenshots/             # 데스크톱 / 모바일 / AI 동작 증빙
```

## 실행 방법

```bash
cd a1-3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env에 아래 환경 변수 세 개를 입력
python3 dev_server.py
```

브라우저에서 `http://localhost:3000`을 엽니다. 로컬 서버도 배포와 동일한
Python 핸들러를 사용하며 공유 링크 경로를 `read.html`로 연결합니다.
로컬 서버는 127.0.0.1에만 연결하고 환경 파일 등 숨김 경로의 요청을 차단합니다.

## 환경 변수

| 이름 | 설명 |
| --- | --- |
| `ANTHROPIC_API_KEY` | Codyssey 과정용 Anthropic 프로토콜 virtual key |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis DB 상세 화면의 REST URL |
| `UPSTASH_REDIS_REST_TOKEN` | 같은 DB의 읽기·쓰기 가능한 REST Token |

키는 `.env` 또는 Vercel 환경 변수에만 넣습니다. `.env`는 Git과 배포에서
제외됩니다. 프론트엔드는 키를 받지 않으며 서버에서 `os.environ`으로만 읽습니다.

이 프로젝트는 `https://copa.codyssey.kr` 게이트웨이에 과정용 키를 보내므로,
일반 Anthropic 공식 API 키를 그대로 넣는 구성이 아닙니다.

## GitHub / Vercel 배포

1. Vercel 프로젝트 `geobulga`에 GitHub `00jup/jeje-codyssey`를 연결합니다.
2. Root Directory는 **`a1-3`**, Framework Preset은 **Other**입니다.
3. 별도 빌드 명령이나 출력 디렉터리를 지정하지 않습니다.
4. 위 환경 변수 세 개를 **Production**에 설정합니다. 프리뷰에서도 AI를
   시험하려면 **Preview**에도 같은 변수를 등록합니다.
5. `main`에 푸시하면 자동 배포됩니다. 환경 변수만 바꾸었다면 최신 배포를
   **Redeploy**해야 적용됩니다.

```bash
git add a1-3
git commit -m "Update travel invitation service"
git push origin main
```

배포 후 https://geobulga.vercel.app에서 메뉴 이동, 모바일 화면, 편지 생성,
공유 링크 조회까지 확인합니다. 실패하면 배포 로그와 브라우저 Network의 상태
코드를 확인하고 수정·커밋·푸시하거나 재배포합니다.

## AI 입력 / 출력 / 실패 처리

- 입력: 상황(기본 여행), 받는 사람 이름, 보내는 사람 이름, 장소(선택),
  사연, 말투, 스티커·사진(선택), 링크 주소(선택).
- 출력: 편지 제목·본문, 버튼 장난 대사, 미리보기, 공유 URL.
- 이름과 사연은 필수입니다. 이름 40자, 장소 60자, 사연 800자까지 받습니다.
- 사진은 최대 2장, 꾸밈은 최대 6개입니다. 브라우저에서 사진을 줄여 전송합니다.
- 빈 입력은 요청 전에 안내하고 입력칸에 포커스를 줍니다.
- 잘못된 JSON/입력 초과는 400, 주소 충돌은 409, 요청 크기 초과는 413입니다.
- AI 인증·호출 한도·네트워크·서버 오류는 사용자용 안내문으로 변환합니다.
- AI 호출은 10초 제한, SDK 자동 재시도는 없습니다. JSON 형식 오류에만 최대
  1회 재시도합니다. 브라우저는 30초가 지나면 지연 안내를 표시합니다.
- 없는/만료된 공유 링크는 404와 안내 화면을 표시합니다.

AI 호출은 사용량을 소모합니다. 생성 중에는 버튼을 비활성화해 중복 제출을
막고, 입력 길이와 재시도 횟수를 제한합니다. 편지 조회·버튼 장난은 AI를 다시
호출하지 않습니다. 공개 API 전체에 적용되는 서버 호출 빈도 제한은 아직 없으므로
제출·개인 공유 용도로 운영하고 제공자 쿼터와 비용을 확인합니다.

## 배운 내용

HTML은 폼과 편지 화면의 구조를, CSS는 배치·색상·반응형·애니메이션을 담당합니다.
JavaScript는 메뉴 전환, 입력 검사, `fetch`, 응답 렌더링과 복사를 담당합니다.

사용자 입력 → JavaScript의 `fetch('/api/compose')` → Vercel Python 함수 →
Claude API → Redis 저장 → JSON 응답 → 미리보기·공유 링크 표시 순서입니다.
받는 사람은 `/api/letter`로 저장된 편지를 조회하며 AI를 다시 호출하지 않습니다.

Vercel 함수는 요청을 받을 때 서버 코드를 실행합니다. 브라우저에 API 키를
넣으면 개발자 도구에서 누구나 읽을 수 있으므로 서버 환경 변수로 관리합니다.
로컬은 `.env`와 개발 서버를 사용하고, 배포는 Vercel이 환경 변수와 함수 실행을
관리합니다. 따라서 로컬 성공만으로 배포 성공을 판단하지 않습니다.

배포 전에 공통 모듈 import 경로와 사진 요청 크기 제한을 수정했습니다.
`compose.py`/`letter.py`가 공통 파일을 읽기 **전에** import 경로를 설정하고,
사진이 포함된 JSON 요청을 받을 수 있도록 본문 상한을 2 MiB로 조정했습니다.

키가 노출되면 발급처에서 즉시 폐기·재발급하고 Vercel 변수를 교체한 뒤
재배포합니다. 저장소에 올라갔다면 관련 커밋 이력에서도 삭제합니다.
