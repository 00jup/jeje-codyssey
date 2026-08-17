# b1-3 — 노코드 자동화 워크플로우 구현

운영 중인 제품(MyMirror · JejeLabs 앱 전체)에서 실제로 쓰는 메시지·운영 대시보드 자동화를 과제 요구에 맞춰 구현·문서화한다.

## 산출물

| 파일 | 내용 |
|---|---|
| [project1-shortcuts-vs-imessage.md](./project1-shortcuts-vs-imessage.md) | **Project 1 도구 비교** — "매주 정시 → 금/토 시간표 분기 → 멘티별 멘토링 확인 iMessage 전송"을 **Apple 단축어 vs AppleScript+launchd**로 구현·비교 |
| [project2-dash-jejelabs.md](./project2-dash-jejelabs.md) | **Project 2 자유 주제** — **JejeLabs 통합 운영 대시보드 `dash.jejelabs.com`**(Cloudflare Workers Cron + D1 + Telegram + Claude API, 실제 운영 시스템 문서화) |
| [build-guide.md](./build-guide.md) | 단축어·AppleScript+launchd **단계별 구현 가이드** + `dash.jejelabs.com` 캡처 가이드 + 스크린샷 체크리스트 |
| `screenshots/` | 구성·실행 결과 캡처 (직접 추가) |

## 두 프로젝트 한눈에

| | Project 1 | Project 2 |
|---|---|---|
| 워크플로우 | 매주 정시 → 금/토 시간표 분기 → 멘티별 멘토링 확인 iMessage 전송 | Cron 3개 → 소스별 수집 → 정상/optional/에러 분기 → 대시보드 6개 탭 + 텔레그램 |
| Trigger | 정해진 시각(단축어 자동화 / launchd `StartCalendarInterval`) | Cloudflare Cron Triggers 3개(KST 07:00/07:20/08:00) |
| Action 2+ | 멘티별 확인 메시지 전송 ×4 (분기별 시간표 문구) | 평점·리뷰·GA4·AdMob·버전 수집 · AI 답글 초안(Claude) · 리포트 발송 |
| 조건 분기 | 금요일 주 / 토요일 주 시간표 | AdMob `optional` 정상 처리 / 실계정 에러 |
| 도구 | 단축어 + AppleScript·launchd (2개) | Cloudflare Workers(Cron)+D1+Telegram+Claude (1개, 코드 기반) |

**Project 2가 노코드 대신 코드 기반 도구를 쓴 이유**: 앱 여러 개 × 데이터 소스 6개(App Store·Play·GA4·AdMob·버전·링크)를 매일 무인 수집·정합화하는 규모라 Make 같은 노코드의 무료 오퍼레이션 한도·모듈 표현력을 넘어섰다. 미션 소개의 "코드 기반 자동화로 확장" 사례로 이미 실제 운영 중인 시스템(`dash.jejelabs.com`)을 그대로 문서화했다. 자세한 선정 근거는 `project2-dash-jejelabs.md` §0 참고.

## 과제 요구사항 매핑

**공통**
- [x] 실제로 동작하는 워크플로우 — 단축어·AppleScript+launchd·`dash.jejelabs.com`(실 운영) 모두 실행됨
- [x] Trigger 1개 이상 — 정해진 시각 / launchd 스케줄 / Cloudflare Cron
- [x] Action 2개 이상 — 멘티별 전송×4(P1) / 소스 수집+리포트 발송(P2)
- [x] 조건 분기 1개 이상 — 금요일/토요일 시간표(P1), 정상·optional/에러(P2)
- [x] 각 분기 경로 1회 이상 실행 결과 — P1 두 분기 구성+토요일 실제 발송+launchd 실행 로그, P2 수집 상태 패널(`미사용`/`실패`/`지연` 표시) 캡처 확보

**Project 1**
- [x] 서로 다른 2개 도구(단축어, AppleScript+launchd)
- [x] 동일 워크플로우 구조
- [x] 비교 보고서: 도구명 · 구현요약 · **10개 비교 항목**(요구 5+) · 장단점 · 적합 상황

**Project 2**
- [x] 반복 업무 1개 정의(앱마다 흩어진 스토어·GA4·AdMob 콘솔을 매일 따로 확인하는 불편)
- [x] 도구 1개 선정 + 선정 이유(Cloudflare Workers 기반 — 왜 노코드가 아닌지 포함)
- [x] Trigger 자동 실행 구조
- [x] 워크플로우 흐름 설명 + 다이어그램 (5개 섹션 각각 "왜 만들었는지" 포함)

**보너스(선택)**
- [x] 보너스 1 — 매일 아침 일일 현황 알림 자동 생성·발송 (Project 2 보너스 구현, 캡처 확보)
- [x] 보너스 2 — 리뷰 답글 Claude 초안 → `/say` 수정 → `/ok` 게시, 실패 시 텔레그램 알림 (캡처 확보)

## ⚠️ 제출 전 체크

- [x] 단축어·AppleScript+launchd 구현 캡처 (남은 것: `p1-launchd-log.png`, `p1-result-launchd-imessage.png`)
- [x] `dash.jejelabs.com` 5개 탭(매출 제외) 캡처
- [x] AdMob 분기 증거 — 수집 상태 패널 캡처(`p2-branch-ingest-status.png`)
- [ ] **민감정보 마스킹** — API 키·토큰·Apple ID·이메일·멘티 이름·연락처·도메인 내부 식별값(vendor number·Property ID 등)은 `***` 처리
