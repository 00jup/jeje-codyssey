# 빌드 가이드 — 클릭해서 캡처만 하면 되게

> 두 프로젝트의 실제 구현 단계. 순서대로 따라 만들고, 각 단계에서 **스크린샷**을 `./screenshots/`에 저장한다.
> ⚠️ 모든 키·토큰·이메일·Apple ID는 캡처 전에 `***`로 가린다.

---

## A. 공통 준비 — Project 1은 별도 가입이 필요 없다

Project 1의 두 도구(단축어, AppleScript+launchd)는 **둘 다 iMessage를 그대로 쓴다.** Mac/iPhone에 로그인된 Apple ID의 iMessage 계정을 그대로 이용하므로 카카오 개발자 앱 등록, OAuth, 토큰 발급 같은 절차가 전혀 없다. 확인할 건 두 가지뿐이다.

1. **설정 → 메시지 → iMessage 활성화** 확인 (Mac은 Messages.app → 설정 → iMessage 로그인 확인)
2. 본인에게 테스트 iMessage를 한 번 보내 정상 수신되는지 확인

---

## B. Project 1 — 단축어(Shortcuts) 구현

### B-1. 자동화(트리거) 만들기
1. 단축어 앱 → **자동화 탭 → + → 개인용 자동화 생성**
2. **특정 시각 → 오전 09:00 → 매주(요일 선택, 예: 수요일)** 선택
3. 하단 **"실행 전에 묻기" 끄기 → "묻지 않음" / 즉시 실행** (무인 실행 핵심)

### B-2. 액션 구성
1. **텍스트** 액션: `True` 또는 `False` — 이번 주 진행 요일 스위치 (True=금요일 주 / False=토요일 주)
2. **만약(If)**: `텍스트 is True`이면 → **메시지 보내기(Send Message)** 액션을 멘티 수만큼 추가 (금요일 시간표 문구)
   - "규원 멘티! 이번 멘토링, 돌아오는 금요일 9시에 괜찮을까요?" → 삼드클 2026 황규원
   - "민규 멘티! 이번 멘토링, 돌아오는 금요일 9시 30분에 괜찮을까요?" → 삼드클 2026 김민규
   - "주원 멘티! 이번 멘토링, 돌아오는 금요일 10시에 괜찮을까요?" → 삼드클 2026 박주원
   - "지강 멘티! 이번 멘토링, 돌아오는 금요일 10시 30분에 괜찮을까요?" → 삼드클 2026 박지강
3. **그 외(Otherwise)**: 같은 멘티들에게 **토요일 시간표 문구**로 메시지 보내기 (토 11시 / 18시 / 18시 30분 / 19시 …)

### B-3. (선택) 전체 공지 단축어 · 멘티 추가
- 별도 단축어 "드림클래스 전체 멘토링 알림": 공지 문구를 변수(`GreetingMessages`)에 담아 멘티 전원에게 일괄 발송
- 멘티가 늘면 각 분기의 **메시지 보내기** 액션을 복제해 수신자·문구만 바꾼다 — 이 "복제 편집"의 번거로움이 도구 B(목록+루프)와의 비교 포인트다

> 📸 캡처: `p1-shortcuts-overview.png`, `p1-shortcuts-actions.png`, `p1-result-shortcuts-imessage.png`

---

## C. Project 1 — AppleScript + launchd 구현

> macOS에 원래 내장된 스크립트(`osascript`)와 스케줄러(`launchd`)만으로 만든다. 단축어가 "GUI 자동화 앱"이라면 이쪽은 "OS 내장 스크립트·데몬 스택"이다 — 이 차이가 비교 포인트.

### C-1. 메시지 전송 스크립트 작성
`~/Scripts/send-imessage.applescript` — 받는 사람·내용을 인자로 받는 범용 전송기:
```applescript
on run argv
  set targetHandle to item 1 of argv
  set msgText to item 2 of argv
  tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy targetHandle of targetService
    send msgText to targetBuddy
  end tell
end run
```
터미널에서 먼저 본인에게 단독 테스트:
```bash
osascript ~/Scripts/send-imessage.applescript "본인 핸들" "테스트 메시지"
```
→ 처음 실행 시 macOS가 **"손쉬운 사용"** 권한을 요구하면 **시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용**에서 터미널(또는 스크립트를 실행하는 앱)을 허용한다.

### C-2. 조건 분기 + 멘티 목록 스크립트
`~/Scripts/mentoring-reminder.sh`:
```bash
#!/bin/zsh
SEND_ENABLED="False"   # 안전 스위치 — True로 바꿔야만 실제 발송
FRIDAY_PLAN="True"     # 조건 분기 — 단축어의 Text(True/False)와 1:1 대응
SCRIPT="$HOME/Scripts/send-imessage.applescript"

FRIDAY_MENTEES=(       # "iMessage 핸들|메시지" — 실제 연락처로 채운다
  "멘티1(***)|규원 멘티! 이번 멘토링, 돌아오는 금요일 9시에 괜찮을까요?"
  "멘티2(***)|민규 멘티! 이번 멘토링, 돌아오는 금요일 9시 30분에 괜찮을까요?"
  "멘티3(***)|주원 멘티! 이번 멘토링, 돌아오는 금요일 10시에 괜찮을까요?"
  "멘티4(***)|지강 멘티! 이번 멘토링, 돌아오는 금요일 10시 30분에 괜찮을까요?"
)
SATURDAY_MENTEES=(
  "멘티1(***)|규원 멘티! 이번 멘토링, 돌아오는 토요일 11시에 괜찮을까요?"
  "멘티2(***)|민규 멘티! 이번 멘토링, 돌아오는 토요일 18시에 괜찮을까요?"
  "멘티3(***)|주원 멘티! 이번 멘토링, 돌아오는 토요일 18시 30분에 괜찮을까요?"
  "멘티4(***)|지강 멘티! 이번 멘토링, 돌아오는 토요일 19시에 괜찮을까요?"
)

[ "$SEND_ENABLED" != "True" ] && { echo "$(date '+%F %T') skipped"; exit 0; }

if [ "$FRIDAY_PLAN" = "True" ]; then MENTEES=("${FRIDAY_MENTEES[@]}"); PLAN="금요일"
else MENTEES=("${SATURDAY_MENTEES[@]}"); PLAN="토요일"; fi

for entry in "${MENTEES[@]}"; do
  osascript "$SCRIPT" "${entry%%|*}" "${entry#*|}"
  sleep 2
done
echo "$(date '+%F %T') sent $PLAN plan to ${#MENTEES[@]} mentees"
```
```bash
chmod +x ~/Scripts/mentoring-reminder.sh
```

### C-3. launchd 스케줄 등록 (Trigger)
`~/Library/LaunchAgents/com.jejelabs.mentoring.plist` — 매주 수요일 09:00 (Weekday: 0=일 … 6=토):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.jejelabs.mentoring</string>
  <key>ProgramArguments</key>
  <array><string>/bin/zsh</string><string>/Users/본인계정/Scripts/mentoring-reminder.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/tmp/mentoring.log</string>
  <key>StandardErrorPath</key><string>/tmp/mentoring.err</string>
</dict>
</plist>
```
등록·실행:
```bash
launchctl load ~/Library/LaunchAgents/com.jejelabs.mentoring.plist
launchctl list | grep mentoring           # 로드 확인
launchctl start com.jejelabs.mentoring    # 즉시 1회 실행 테스트 (스위치 False면 스킵 알림만 옴)
cat /tmp/mentoring.log /tmp/mentoring.err # 발송/스킵 기록·실패 원인 확인
```

### C-4. 결과 확인 (두 분기 경로)
- 멘티 핸들을 채우고 `SEND_ENABLED="True"`로 바꾼 뒤 (실수 발송 주의 — 캡처 후 다시 `False`로):
  - `FRIDAY_PLAN="True"`로 1회 실행 → 금요일 시간표 문구 발송 확인
  - `FRIDAY_PLAN="False"`로 1회 실행 → 토요일 시간표 문구 발송 확인
- `launchctl list`로 로드 상태, `/tmp/mentoring.log`로 발송/스킵 이력 확인 (단축어보다 로그가 남는다 = 비교 포인트)

> 📸 캡처: `p1-mentoring-script.png`, `p1-applescript.png`, `p1-launchd-plist.png`, `p1-launchd-log.png`, `p1-result-launchd-imessage.png`

---

## D. Project 2 — `dash.jejelabs.com` 캡처 가이드

Project 2는 **처음부터 새로 빌드하는 것이 아니라 이미 운영 중인 시스템**(`jejelabs-metrics` 리포지토리, Cloudflare Workers + D1 + Telegram + Claude API)을 문서화한다. 아래는 그 실물에서 "구현 화면"과 "실행 결과"를 캡처하는 순서다.

### D-1. 구성(구현) 화면
1. Cloudflare 대시보드 → Workers → `jejelabs-metrics` → **Triggers** 탭 — Cron 3개 목록 (계정 정보는 마스킹)
2. **Settings → Domains & Routes** — `dash.jejelabs.com` 라우트 연결 화면
3. Cloudflare **Zero Trust → Access → Applications** — `dash.jejelabs.com` 보호 규칙(팀 도메인 등은 마스킹)
4. `wrangler.jsonc`의 `crons` 설정 부분 (시크릿 없음, 그대로 캡처 가능)

### D-2. 대시보드 탭 실행 결과 (매출 탭 제외 5개)
`dash.jejelabs.com` 접속(Access 로그인 필요) 후 각 탭 캡처 — 매출 탭은 수익 정보 노출을 피해 캡처에서 제외한다:
1. **앱(분석)** — DAU·MAU 등 GA4 지표 화면
2. **웹** — Cloudflare Web Analytics 사이트 트래픽 화면
3. **리뷰** — 리뷰 대응 현황·AI 답글 화면
4. **출시** — 버전·심사 상태 화면
5. **링크** — 링크 생사 확인 화면

### D-3. 조건 분기 — 두 경로 실행 증거
- 대시보드 하단 **"수집 상태" 패널** 한 장으로 두 경로를 보인다: AdMob 카드의 `미사용`(optional 정상 처리), 실패 시 같은 카드의 `error` 표시(부분 실패는 "실패 N" 인라인, 오래 안 돈 수집은 `지연`) — `p2-branch-ingest-status.png`

### D-4. 보너스 캡처
- **보너스 1(매일 아침 알림)**: 텔레그램 봇의 08:00 일일 현황 리포트 메시지 — `p2-bonus-daily-report.png`
- **보너스 2(리뷰 게시+실패 알림)**: `/draft`(Claude 초안) → `/say`(수정) → `/ok`(게시) 흐름 — `p2-bonus-ai-draft.png`, `p2-branch-edit.png`

> 📸 캡처: `p2-tab-analytics.png`, `p2-tab-web.png`, `p2-tab-reviews.png`, `p2-tab-releases.png`, `p2-tab-links.png`, `p2-branch-ingest-status.png`, `p2-bonus-daily-report.png`, `p2-bonus-ai-draft.png`, `p2-branch-edit.png`

---

## E. 스크린샷 체크리스트

`b1-3/screenshots/` 폴더에 저장. 캡처 전 민감정보(Apple ID·API 키·토큰·계정 이메일·도메인 내부 값) `***` 마스킹 필수.

**Project 1**
- [x] `p1-shortcuts-overview.png` — 전체 알림 단축어 구성
- [x] `p1-shortcuts-actions.png` — If True(금요일 시간표) 분기 액션
- [x] `p1-shortcuts-otherwise.png` — Otherwise(토요일 시간표) 분기 액션
- [x] `p1-result-shortcuts-imessage.png` — 실제 발송된 iMessage 대화창
- [x] `p1-mentoring-script.png` — 분기·멘티 목록 셸 스크립트
- [x] `p1-applescript.png` — AppleScript 스크립트 내용
- [x] `p1-launchd-plist.png` — launchd plist 파일
- [x] `p1-launchd-log.png` — `launchctl list` / 실행 로그
- [x] `p1-result-launchd-imessage.png` — 자동 발송된 iMessage 수신 대화창(김예준)

**Project 2**
- [x] `p2-tab-analytics.png` / `p2-tab-web.png` / `p2-tab-reviews.png` / `p2-tab-releases.png` / `p2-tab-links.png` — 5개 탭(매출 제외)
- [x] `p2-branch-ingest-status.png` — 수집 상태 패널(AdMob `미사용` 정상 처리 + 실패 시 `error`·`지연` 표시)
- [x] (보너스 1) `p2-bonus-daily-report.png` — 매일 아침 텔레그램 일일 현황
- [x] (보너스 2) `p2-bonus-ai-draft.png` / `p2-branch-edit.png` — `/draft` 초안 → `/say` 수정 → `/ok` 게시
