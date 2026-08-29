# 제출용 스크린샷

아래 이름 그대로 넣으면 [`../README.md`](../README.md) 의 8절 표와 맞는다.

## 준비

```bash
cd a1-3
source .venv/bin/activate
python3 dev_server.py     # 또는 배포 URL 로 찍는다 — 배포본이 더 좋다
```

**배포 URL로 찍는 편이 낫다.** 주소창에 `.vercel.app` 도메인이 보이면 그 자체가
"배포된 서비스가 동작한다"는 증빙이 된다.

## 찍기 전에 확인

- 주소창에 API 키가 들어간 쿼리스트링이 없는지
- 개발자 도구가 열려 있다면 Network 탭에 키가 보이지 않는지
- `.env` 파일이 열린 에디터가 화면에 같이 찍히지 않는지

## desktop/ — 브라우저 폭 1440px 정도

| 파일 | 무엇을 |
| --- | --- |
| `01-home.png` | 홈 화면 전체. 상단 메뉴 5개가 보이게 |
| `02-draft-result.png` | **타래 짓기** — 소재를 넣고 초안이 나온 상태. 입력칸과 조각 카드가 한 화면에 |
| `03-reply-result.png` | **답글 짓기** — 영어 댓글을 넣어 영어 답글이 나온 상태 (언어 배지가 보이게) |
| `04-error.png` | 빈 입력으로 제출해 안내 문구가 뜬 상태 |
| `05-dark.png` | 헤더의 테마 버튼을 눌러 다크 모드로 바꾼 화면 |

## mobile/ — 실제 폰 또는 개발자 도구 디바이스 툴바(iPhone 14 Pro, 390px)

| 파일 | 무엇을 |
| --- | --- |
| `01-home.png` | 홈. 햄버거 버튼이 보이게 |
| `02-menu.png` | 햄버거를 눌러 메뉴가 펼쳐진 상태 |
| `03-draft-result.png` | 모바일에서 초안 결과가 나온 화면 |

## ai-tool/ — AI 코딩 도구 사용 과정

| 파일 | 무엇을 |
| --- | --- |
| `01-requirements.png` | 무엇을 만들지 지시한 대화 |
| `02-api-implementation.png` | 서버리스 함수를 만들어 가는 과정 |
| `03-debugging.png` | 오류를 잡는 과정 |
| `04-verification.png` | `curl` 로 엔드포인트를 검증하는 화면 |

무엇을 담을지는 [`../docs/ai-coding-log.md`](../docs/ai-coding-log.md) 4절 참고.
