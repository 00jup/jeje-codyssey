# 빌드 가이드 — 클릭해서 캡처만 하면 되게

> 두 프로젝트의 실제 구현 단계. 순서대로 따라 만들고, 각 단계에서 **스크린샷**을 `./screenshots/`에 저장한다.
> ⚠️ 모든 키·토큰·이메일은 캡처 전에 `***`로 가린다.

---

## A. 공통 준비 — 카카오 '나에게 보내기' API (Project 1용)

본인 카톡 "나와의 채팅"으로 메시지를 보내는 API다. 친구 전송이 아니라 **본인 전송**이라 별도 검수가 필요 없다.

1. [Kakao Developers](https://developers.kakao.com) 로그인 → **내 애플리케이션 → 애플리케이션 추가하기**
2. 생성된 앱 → **앱 키**에서 `REST API 키` 확인 (캡처 시 마스킹)
3. **카카오 로그인 → 활성화 ON**, **Redirect URI** 등록 (예: `https://localhost`)
4. **카카오 로그인 → 동의항목**에서 `talk_message`(카카오톡 메시지 전송) 권한 ON
5. **토큰 발급** (1회):
   - 인가코드 받기(브라우저):
     ```
     https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri=https://localhost&response_type=code&scope=talk_message
     ```
   - 리다이렉트 URL의 `code=` 값으로 토큰 교환:
     ```bash
     curl -X POST "https://kauth.kakao.com/oauth/token" \
       -d "grant_type=authorization_code" \
       -d "client_id={REST_API_KEY}" \
       -d "redirect_uri=https://localhost" \
       -d "code={인가코드}"
     ```
   - 응답의 `access_token`(약 6~12시간) · `refresh_token`(약 2개월) 보관
6. **전송 테스트**:
   ```bash
   curl -X POST "https://kapi.kakao.com/v2/api/talk/memo/default/send" \
     -H "Authorization: Bearer {ACCESS_TOKEN}" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode 'template_object={"object_type":"text","text":"테스트 메시지","link":{"web_url":"https://fns.tools"}}'
   ```
   → 카톡 "나와의 채팅"에 도착하면 성공.

> **토큰 갱신**(access token 만료 시):
> ```bash
> curl -X POST "https://kauth.kakao.com/oauth/token" \
>   -d "grant_type=refresh_token" -d "client_id={REST_API_KEY}" -d "refresh_token={REFRESH_TOKEN}"
> ```

---

## B. Project 1 — 단축어(Shortcuts) 구현

### B-1. 자동화(트리거) 만들기
1. 단축어 앱 → **자동화 탭 → + → 개인용 자동화 생성**
2. **특정 시각 → 오전 08:00 → 매일** 선택
3. 하단 **"실행 전에 묻기" 끄기 → "묻지 않음" / 즉시 실행** (무인 실행 핵심)

### B-2. 액션 구성
1. **현재 날짜 가져오기** → **날짜 구성요소(요일)** 추출
2. **만약(If)**: 요일이 `토요일` 또는 `일요일`이면
   - (주말) **텍스트**: `🌿 주말입니다. 오늘 할 일 1개만 적어두기`
   - (그 외 = 평일) **텍스트**: `📊 어제 총 사용자 / 다운로드 확인` (GA 1줄을 넣으려면 아래 B-3)
3. **텍스트**(token 보관): `{ACCESS_TOKEN}` — 또는 refresh 호출 액션 먼저
4. **URL의 콘텐츠 가져오기(Get Contents of URL)**:
   - URL: `https://kapi.kakao.com/v2/api/talk/memo/default/send`
   - 방식: `POST`
   - 헤더: `Authorization` = `Bearer {ACCESS_TOKEN}`
   - 본문: `양식(Form)` → `template_object` = `{"object_type":"text","text":"<위 분기 텍스트>","link":{"web_url":"https://fns.tools"}}`

### B-3. (선택) 평일에 GA 1줄 넣기
- 평일 경로에 **URL의 콘텐츠 가져오기** 하나 더 추가 → GA4 runReport(아래 D 참고) 호출 → 응답에서 `activeUsers` 추출 → 메시지 텍스트에 끼워넣기

> 📸 캡처: `p1-shortcuts-overview.png`, `p1-shortcuts-actions.png`, `p1-result-shortcuts-kakao.png`

---

## C. Project 1 — Make 구현

1. **새 시나리오** 생성
2. **Schedule** 트리거 추가 → `Every day, 08:00`
3. (토큰) 첫 모듈로 **HTTP > Make a request** → 카카오 token refresh 호출(또는 Connections에 카카오 OAuth2 커넥션 저장)
4. **Tools > Set variable**: 오늘 요일 계산 (`formatDate(now; "dddd")`)
5. **Router** 추가 → 두 경로:
   - 경로 1 **Filter**: 요일 = 평일 → 메시지 = GA 1줄 (평일 경로에 GA4 조회 HTTP 모듈 추가)
   - 경로 2 **Filter**: 요일 = 주말 → 메시지 = 리마인더
6. 각 경로 끝에 **HTTP > Make a request**:
   - URL: `https://kapi.kakao.com/v2/api/talk/memo/default/send` / `POST`
   - Header: `Authorization: Bearer {{token}}`
   - Body type: `application/x-www-form-urlencoded`, field `template_object` = 위 JSON
7. **Run once**로 즉시 실행 테스트 → 실행 히스토리 확인

> 📸 캡처: `p1-make-scenario.png`, `p1-make-router.png`, `p1-result-make-history.png`, `p1-result-weekday.png`, `p1-result-weekend.png`

---

## D. Project 2 — GA4 Data API 준비

### D-1. Property ID 확인
- GA4 → **관리 → 속성 설정**에서 각 속성의 **숫자 속성 ID**(예: `123456789`) 확인
- MyMirror / fns 앱 / fns-web 세 개 모두

### D-2. 인증 (둘 중 택1)
- **(권장) 서비스 계정**: Google Cloud → 서비스 계정 생성 → JSON 키 발급 → 각 GA4 속성의 **관리 → 속성 액세스 관리**에 서비스 계정 이메일을 **뷰어**로 추가. 토큰 갱신 불필요
- **OAuth 사용자**: 세 속성에 접근 권한 있는 구글 계정으로 OAuth(`analytics.readonly`). Make의 Google 커넥션이 갱신 처리

### D-3. runReport 호출 형태
```
POST https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY_ID}:runReport
Authorization: Bearer {GOOGLE_ACCESS_TOKEN}
Content-Type: application/json

{
  "dateRanges": [
    { "startDate": "yesterday", "endDate": "yesterday" },
    { "startDate": "2daysAgo",  "endDate": "2daysAgo" }
  ],
  "metrics": [
    { "name": "activeUsers" }, { "name": "newUsers" },
    { "name": "sessions" },    { "name": "eventCount" }
  ]
}
```
- 두 개의 dateRange(어제·그제)를 함께 요청해 **전일 대비 변동률**을 계산 → 조건 분기에 사용

---

## E. Project 2 — Make 구현

1. **새 시나리오** → **Schedule** 트리거 `Every day, 09:00`
2. **세 속성 조회**: `HTTP > Make a request`(또는 Make의 Google Analytics 모듈) 3개 — 각 Property ID로 D-3 본문 호출
   - 또는 **Iterator**로 Property ID 배열을 순회해 모듈 1개로 반복
3. **Tools > Set variable**로 속성별 변동률 계산
4. **Router** → ⚠️강조 경로(±20%↑) / 일반 경로 — 각 경로 **Filter**
5. **Text aggregator / Set variable**로 세 결과를 **HTML 표 한 개**로 합치기
6. **Email > Send an email**(또는 HTTP로 Resend) — 합친 표를 본문으로 발송
7. (보너스 1) 발송 전 **HTTP > Claude/GPT API** 호출해 요약 한 줄 추가
8. (보너스 2) **Error handler** 라우트: 실패 시 카카오/메일 알림 + 임시 Google Sheets `Add a Row`
9. **Run once** → 메일 수신 확인 → 실행 히스토리 캡처

> 📸 캡처: `p2-make-scenario.png`, `p2-make-ga-module.png`, `p2-result-email.png`, `p2-branch-alert.png`, `p2-branch-normal.png`, (보너스) `p2-bonus-ai.png`, `p2-bonus-errorflow.png`

---

## F. 스크린샷 체크리스트

`b1-3/screenshots/` 폴더에 저장. 캡처 전 민감정보 `***` 마스킹 필수.

**Project 1**
- [ ] `p1-shortcuts-overview.png` — 단축어 자동화 목록
- [ ] `p1-shortcuts-actions.png` — 단축어 액션 구성
- [ ] `p1-make-scenario.png` — Make 시나리오 캔버스
- [ ] `p1-make-router.png` — Router/Filter 분기
- [ ] `p1-result-weekday.png` / `p1-result-weekend.png` — 분기별 수신 메시지
- [ ] `p1-result-shortcuts-kakao.png` / `p1-result-make-history.png` — 실행 결과

**Project 2**
- [ ] `p2-make-scenario.png` — 시나리오 전체
- [ ] `p2-make-ga-module.png` — GA4 조회 모듈
- [ ] `p2-result-email.png` — 통합 리포트 수신 메일
- [ ] `p2-branch-alert.png` / `p2-branch-normal.png` — 분기 경로
- [ ] (보너스) `p2-bonus-ai.png` / `p2-bonus-errorflow.png`
```
