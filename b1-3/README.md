# b1-3 — 노코드 자동화 워크플로우 구현

운영 중인 제품(MyMirror · fns 앱 · fns-web)에서 실제로 쓰는 메일·메시지 자동화를 과제 요구에 맞춰 구현·문서화한다.

## 산출물

| 파일 | 내용 |
|---|---|
| [project1-shortcuts-vs-make.md](./project1-shortcuts-vs-make.md) | **Project 1 도구 비교** — "정시 → 분기 → 카카오 '나에게 보내기'"를 **Apple 단축어 vs Make**로 구현·비교 |
| [project2-ga-daily-report.md](./project2-ga-daily-report.md) | **Project 2 자유 주제** — 멀티 GA4(MyMirror·fns앱·fns-web) **통합 일일 리포트 메일** (Make) |
| [build-guide.md](./build-guide.md) | 단축어·Make·카카오 API·GA4 Data API **단계별 구현 가이드** + 스크린샷 체크리스트 |
| `screenshots/` | 구성·실행 결과 캡처 (직접 추가) |

## 두 프로젝트 한눈에

| | Project 1 | Project 2 |
|---|---|---|
| 워크플로우 | 정시 → 평일/주말 분기 → 카톡 '나에게 보내기' | 멀티 GA4 → 급변/정상 분기 → 통합 메일 |
| Trigger | 정해진 시각(단축어 자동화 / Make 스케줄) | 매일 09:00 스케줄 |
| Action 2+ | 메시지 조립 · 카톡 API 전송 (평일 GA 조회) | GA 3속성 조회 · 표 합치기 · 메일 발송 |
| 조건 분기 | 평일 / 주말 | 전일 대비 ±20% 급변 / 정상 |
| 도구 | 단축어 + Make (2개) | Make (1개) |

## 과제 요구사항 매핑

**공통**
- [x] 실제 동작하는 워크플로우 — 단축어·Make에서 실행
- [x] Trigger 1개 이상 — 정해진 시각 / 스케줄
- [x] Action 2개 이상 — 메시지/표 조립 + 전송/발송
- [x] 조건 분기 1개 이상 — 평일/주말, 급변/정상
- [ ] 각 분기 경로 1회 이상 실행 결과 — **스크린샷 추가 필요**

**Project 1**
- [x] 서로 다른 2개 도구(단축어, Make)
- [x] 동일 워크플로우 구조
- [x] 비교 보고서: 도구명 · 구현요약 · **9개 비교 항목**(요구 5+) · 장단점 · 적합 상황

**Project 2**
- [x] 반복 업무 1개 정의(여러 GA를 따로 보는 불편)
- [x] 도구 1개 선정 + 선정 이유(Make)
- [x] Trigger 자동 실행 구조
- [x] 워크플로우 흐름 설명 + 다이어그램

**보너스(선택)**
- [ ] 보너스 1 — AI 요약 Action (Project 2 §5)
- [ ] 보너스 2 — 실패 알림·재시도·대체 경로 (Project 2 §5)

## ⚠️ 제출 전 체크

- [ ] `build-guide.md` 따라 단축어·Make 실제 구현 후 캡처
- [ ] 두 분기 경로가 모두 실행된 결과 캡처
- [ ] **민감정보 마스킹** — API 키·토큰·OAuth·이메일·Property ID는 `***` 처리
```
