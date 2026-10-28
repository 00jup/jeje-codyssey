# StoreSense AI — 스마트스토어 매출 분석 비서 (m1-2)

일반적인 ChatGPT는 우리 매장의 개별 매출 데이터를 알지 못합니다. "이번 달 매출이 어때?"라고 물어도 일반적인 상식만 답변합니다.  
**StoreSense AI**는 저장된 일별 시계열 매출 데이터를 실시간 분석·요약하고, 이를 프롬프트에 주입(Context Injection)하여 **"내 매장 상황을 속속들이 아는 맞춤형 AI 비서"**를 제공하는 풀스택 웹 애플리케이션입니다.

---

## 1. 서비스 개요 및 해결 과제

- **서비스명**: StoreSense AI (스마트스토어 일별 매출 분석 비서)
- **해결하는 문제**: 
  - 분산된 매출 데이터를 직관적으로 관리(CRUD)
  - 100일 이상의 시계열 데이터를 바탕으로 일평균, 최고/최저 실적, 성장 트렌드 자동 산출
  - 데이터 요약을 주입받은 AI 비서가 점주님의 자연어 질문에 정확한 근거와 비즈니스 인사이트를 제시
- **배포 URL**:
  - **프론트엔드 (Vercel)**: `https://frontend-omega-tawny-50.vercel.app`
  - **백엔드 API (Vercel)**: `https://storesense-api.vercel.app`
  - **Swagger API 문서**: `https://storesense-api.vercel.app/docs`

---

## 2. 기술 스택

| 영역 | 기술 스택 | 설명 |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | 고성능 비동기 RESTful API 서버, 라우터/서비스 계층 분리 |
| **Data Validation** | Pydantic v2 | 요청/응답 스키마 엄격 검증 및 자동 문서화(OpenAPI) |
| **Database** | Google Cloud Firebase Firestore | NoSQL 문서 기반 DB (`data`, `conversations` 컬렉션) |
| **AI / LLM** | OpenAI API (`gpt-4o-mini`) | 시계열 요약 정보 컨텍스트 주입 기반 자연어 생성 |
| **Frontend** | Vanilla HTML5, Modern CSS3, JavaScript (ES6+) | 프레임워크 없는 순수 바닐라 웹 앱 (SPA 대시보드) |
| **Deployment** | Vercel (프론트엔드·백엔드) | 클라우드 플랫폼 배포 및 환경 변수 기반 운영 |

---

## 3. 핵심 기능 구현 내용

### 1) 시계열 데이터 관리 (CRUD)
- `POST /api/data`: `(date, value, memo)` 형태의 신규 일별 매출 등록
- `GET /api/data`: 날짜순 정렬된 전체 시계열 데이터 목록 조회
- `PUT /api/data/{id}`: 특정 날짜의 매출 데이터 수정
- `DELETE /api/data/{id}`: 특정 매출 데이터 삭제
- `GET /api/data/summary`: 전체 시계열 데이터 통계(기간, 총개수, 총합, 일평균, 최고/최저일, 트렌드) 계산 반환
- **기본 예시 데이터 탑재**: 최초 실행 시 120일치(약 4개월)의 현실적인 시계열 매출 데이터가 자동으로 적재되어 즉시 분석 가능

### 2) 데이터 요약 및 컨텍스트 주입 (Context Injection)
- `GET /api/data/summary`로 도출된 핵심 지표를 시스템 프롬프트(System Prompt)에 동적으로 주입
- AI가 환각(Hallucination) 없이 실제 점포의 누적 매출, 일평균, 최고 실적일, 최근 성장률을 바탕으로 사실 기반 답변 생성

### 3) 대화 기록 세션 관리 (Conversations)
- `POST /api/conversations`: 대화 세션 및 메시지 생성/저장
- `GET /api/conversations`: 이전 대화 목록 조회
- `GET /api/conversations/{id}`: 특정 대화의 전체 메시지 조회 (불러오기 UX)
- `DELETE /api/conversations/{id}`: 대화 기록 삭제
- `POST /api/chat` 호출 시 자동으로 `conversations` 컬렉션에 유저 질문과 AI 답변이 멀티턴 형식으로 영구 저장

### 4) 반응형 바닐라 프론트엔드 UX
- **실시간 요약 대시보드 위젯**: 기간, 총 데이터 수, 누적 매출, 일평균, 최고 실적, 트렌드 뱃지 한눈에 표시
- **채팅 인터페이스**: 타이핑 인디케이터(로딩 표시), 추천 질문 원클릭 칩, 실시간 스크롤
- **데이터 관리 테이블**: 인라인 모달을 통한 데이터 추가 및 수정, 즉시 삭제 지원
- **사이드바 대화 기록**: 이전 상담 내역 원클릭 불러오기 및 새 대화 시작

---

## 4. 환경 변수 설정 (.env)

백엔드 실행을 위해 프로젝트 루트 또는 `backend/` 디렉터리에 `.env` 파일을 생성합니다.

```ini
# OpenAI API 설정
OPENAI_API_KEY=sk-...your-openai-api-key...
OPENAI_MODEL=gpt-4o-mini

# Firebase Firestore 연동 (아래 중 1가지 선택)
# 방법 A: 서비스 계정 키 파일 경로 지정
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-service-account.json
# 방법 B: Vercel 배포 등에서 JSON 문자열 통째로 지정할 때
# FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# CORS 허용 도메인 (쉼표 구분)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:5500,https://*.vercel.app,*

# 서버 포트 (기본 8000)
PORT=8000
```

> [!NOTE]
> Firebase 서비스 계정 키나 OpenAI API 키가 아직 설정되지 않은 개발 상태에서도 안전하게 **로컬 Fallback 모드**로 작동하여 즉시 UI와 API를 테스트할 수 있습니다. 키가 입력되면 자동으로 Firestore 및 GPT API와 실제 통신합니다.

---

## 5. 로컬 실행 방법

### 1) 백엔드 실행 (FastAPI)
```bash
# 가상환경 활성화 (Python 3.10 이상)
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 백엔드 서버 시작
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- 브라우저에서 `http://localhost:8000` 접속 시 통합 웹 앱 실행
- API 대화형 문서는 `http://localhost:8000/docs` (Swagger UI)에서 확인

### 2) 프론트엔드 단독 실행 (옵션)
프론트엔드 정적 파일은 백엔드에서 기본 서빙되지만, Vercel 개발 환경이나 Live Server로 단독 실행할 수도 있습니다.
```bash
cd frontend
python3 -m http.server 3000
```
- 브라우저에서 `http://localhost:3000` 접속 후 우측 상단의 `⚙️ API 설정` 버튼을 통해 백엔드 주소(`http://localhost:8000` 등)를 지정할 수 있습니다.

---

## 6. 과제 목표 기술 설명 (Self-Review)

### Q1. 시계열 데이터를 분석하고 요약 정보를 만들어 서비스에서 활용하는 흐름은?
1. Firestore의 `data` 컬렉션에서 `(date, value, memo)` 레코드들을 날짜순으로 조회합니다.
2. `AnalysisService`가 시계열 데이터를 순회하며 분석 기간(`first_date ~ last_date`), 총 데이터 개수(`count`), 누적합(`total`), 일평균(`average`), 최고치(`max`)와 발생일자(`max_date`), 최저치(`min`)와 발생일자(`min_date`)를 계산합니다.
3. 최근 n일(예: 30일)의 평균과 직전 기간의 평균을 분할 비교하여 성장/하락/보합 트렌드(증감률 %)를 계산합니다.
4. 이 정제된 `DataSummary` 객체를 프론트엔드 대시보드 위젯에 노출함과 동시에, AI 챗봇 호출 시 시스템 프롬프트에 텍스트 형태로 주입하여 일관된 데이터 기반 답변을 유도합니다.

### Q2. FastAPI 프로젝트를 라우터/서비스 등으로 분리해 구성한 기준은?
- **`app/models` (데이터 계층)**: Pydantic을 활용해 요청 및 응답 데이터의 스키마와 데이터 타입을 엄격하게 정의합니다.
- **`app/services` (비즈니스 계층)**: DB 연동(`FirebaseService`), 통계 계산 알고리즘(`AnalysisService`), 외부 LLM 통신(`AIService`) 등 순수 비즈니스 로직을 캡슐화하여 테스트와 유지보수를 용이하게 합니다.
- **`app/routers` (표현/라우팅 계층)**: HTTP 엔드포인트 매핑, 상태 코드, 의존성 주입, 예외 처리(`HTTPException`)만을 전담합니다.
- **`app/main.py`**: 미들웨어(CORS) 설정, 라우터 통합, 정적 파일 서빙 등 애플리케이션 수명주기를 관리합니다.

### Q3. Pydantic을 활용해 요청 데이터 검증을 적용한 이유와 방식은?
- 클라이언트가 전달하는 `date` 문자열 형식, `value`의 0 이상 양수 여부(`ge=0`), `memo`의 최대 글자 수(`max_length=300`) 등을 런타임에 자동 검증하여 잘못된 데이터 유입을 사전에 차단합니다.
- 검증 실패 시 상세한 422 Unprocessable Entity 에러를 반환하며, 정의된 스키마가 Swagger UI 문서에 자동으로 반영되어 API 문서화 작업이 자동화됩니다.

### Q4. Firestore에 데이터를 저장하고 CRUD로 다루는 방법은?
- `firebase-admin` 라이브러리의 `firestore.client()`를 사용해 `data`와 `conversations` 두 개의 독립 컬렉션을 구성했습니다.
- `create`: `db.collection("data").document(id).set(record)`
- `read`: `.order_by("date").stream()` 및 `.document(id).get()`
- `update`: `doc_ref.update(cleaned_updates)`
- `delete`: `doc_ref.delete()`
- 서비스 계정 키는 `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` 또는 `FIREBASE_SERVICE_ACCOUNT_JSON` 환경 변수로 안전하게 주입받아 초기화합니다.

### Q5. "데이터 요약을 시스템 프롬프트에 주입하는 방식(컨텍스트 주입)"의 원리는?
- LLM 모델 자체는 외부 비공개 데이터베이스에 직접 접근할 수 없으므로, 사용자의 질문이 전달되기 전 서버 레벨에서 최신 `DataSummary`를 문자열 포맷팅하여 시스템 프롬프트에 동적으로 삽입합니다.
- 이를 통해 모델은 사전 학습 지식이 아닌 **시스템 프롬프트에 명시된 점포의 실제 매출 수치와 통계 사실(Fact)**만을 기준으로 정확한 답변을 생성하게 되며, 환각(Hallucination) 현상을 방지합니다.

### Q6. 배포 환경에서 CORS / 환경변수 / 키 관리가 왜 필요한지?
- **CORS (Cross-Origin Resource Sharing)**: 프론트엔드와 백엔드가 서로 다른 Vercel 도메인에 호스팅되므로 브라우저의 동일 출처 정책(SOP)에 차단되지 않도록 허용 오리진을 설정해야 합니다.
- **환경 변수 및 키 관리**: OpenAI API 키나 Firebase 서비스 계정 키 같은 비밀 인증 정보를 Git 저장소에 하드코딩하면 심각한 보안 침해와 크레딧 탈취가 발생할 수 있으므로, Vercel Environment Variables로 격리하여 안전하게 주입해야 합니다.

---

## 7. 제출 스크린샷 가이드

과제 제출 시 아래 3가지 화면을 캡처하여 첨부합니다:

1. **데이터 요약이 보이는 채팅 화면**:
   - 상단 요약 카드(기간, 총영업일, 누적 매출, 일평균, 트렌드)와 함께 사용자의 질문("이번 달 실적이 어때?") 및 AI 비서의 맞춤 답변이 함께 보이는 화면
2. **데이터 관리 화면 (CRUD)**:
   - "📋 매출 데이터 관리" 탭에서 120개의 시계열 데이터 테이블과 새 데이터 추가 모달 또는 수정/삭제 완료 토스트가 보이는 화면
3. **대화 기록 화면**:
   - 왼쪽 사이드바에 저장된 이전 대화 목록이 표시되고, 특정 대화를 클릭하여 이전 메시지들이 메인 채팅창에 정상 재표시(불러오기)된 화면
