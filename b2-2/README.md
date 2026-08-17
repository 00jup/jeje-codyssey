# b2-2: API 활용 국내 여행지 추천 프로그램

Gemini API(LLM)와 Kakao Local API(지도/장소 검색)를 조합한 CLI 기반 국내 여행 추천 프로그램이다. 여행 날짜를 입력하면 다음 순서로 동작한다.

1. Gemini가 해당 시기에 여행하기 좋은 국내 지역을 JSON으로 1차 추천한다 (`recommended_city`, `weather`, `events`, `reason`).
2. Kakao Local API로 추천 지역의 맛집 5곳을 검색한다.
3. Gemini가 1차 추천 정보 + 맛집 목록을 종합해 최종 여행 리포트를 Markdown으로 생성한다.

## 실행 방법

```bash
cd b2-2
pip install -r requirements.txt
python travel_planner.py --date "2026-03-15"
```

성공하면 아래와 같은 로그가 출력되고, `results/` 폴더에 결과 파일이 생성된다.

```
[1/3] 1차 추천 생성 중(LLM)...
    - recommended_city: "제주"
[2/3] 맛집 검색 중(지도/장소 API)...
    - 맛집 5곳 검색 완료
[3/3] 최종 리포트 생성 중(LLM)...
    - 리포트 생성 완료

완료! results/2026-03-15_travel_plan.md 를 확인하세요.
```

같은 `--date`로 다시 실행하면 이미 저장된 원본 JSON을 재사용해 API 호출(1, 2단계)을 건너뛰고 리포트만 다시 생성한다(캐싱).

## API 키 설정 방법

1. `.env.example`을 복사해 `.env` 파일을 만든다.
   ```bash
   cp .env.example .env
   ```
2. `.env` 파일을 열어 아래 두 값을 채운다.
   - `GEMINI_API_KEY`: [Google AI Studio](https://aistudio.google.com/apikey)에서 발급.
   - `KAKAO_REST_API_KEY`: [Kakao Developers](https://developers.kakao.com/) 콘솔 > 내 애플리케이션 > 앱 키 > **REST API 키**.
     - Kakao Local API가 401/403을 반환하면 앱 키 값과 "플랫폼 > Web" 도메인 등록 여부를 점검한다.
3. 키를 설정하지 않고 실행하면 프로그램이 즉시 종료되며, 어떤 키가 빠졌는지와 설정 방법을 안내한다.

## API 키 유출 주의 사항

- API 키는 코드에 직접 작성하지 않으며, 반드시 `.env` 파일 또는 환경변수로만 관리한다.
- `.env`는 `.gitignore`에 등록되어 있어 커밋되지 않는다. **`.env` 파일을 절대 직접 `git add`하거나 캡처/공유하지 않는다.**
- `results/`에 저장되는 원본 JSON과 리포트 Markdown에는 API 키가 포함되지 않는다(추천/검색 결과 데이터만 저장).
- 키가 실수로 노출됐다면 즉시 발급처(Google AI Studio / Kakao Developers)에서 키를 재발급(rotate)한다.

## 결과물 확인 방법

`results/` 폴더에 실행할 때마다 아래 2개 파일이 생성(또는 갱신)된다.

- `results/{YYYY-MM-DD}_raw_data.json`: 1차 추천 JSON, 맛집 검색 결과(배열, 0건 가능), 오류 요약(`errors`)을 포함한 원본 데이터.
- `results/{YYYY-MM-DD}_travel_plan.md`: 추천 지역/이유, 날씨, 행사/축제, 맛집 리스트, 1일 일정 제안, 오류 요약이 담긴 최종 리포트.

## 에러 처리 정책

- **API 키 미설정**: 즉시 종료 + 설정 방법 안내 출력.
- **장소 검색 실패**(네트워크/인증/쿼터 등) 또는 **검색 결과 0건**: 맛집 섹션을 "데이터 없음"으로 표기하고 리포트 생성은 계속 진행. `errors` 배열에 `AUTH_ERROR` / `NETWORK_ERROR` / `HTTP_ERROR` / `EMPTY_RESULT` 로 기록.
- **1차 추천 LLM의 JSON 파싱 실패**: 필수 키만 다시 출력하도록 프롬프트를 수정해 최대 1회 재시도. 재시도까지 실패하면 프로그램을 종료한다.
- **최종 리포트 생성 LLM 호출 실패**: 이미 확보된 데이터로 로컬 템플릿을 사용해 리포트를 대체 생성하므로 결과 파일은 항상 만들어진다.

## 필드 참고

- 맛집 아이템의 `x`, `y`는 Kakao Local API 원본 필드로 각각 경도(longitude), 위도(latitude) 문자열이다.
