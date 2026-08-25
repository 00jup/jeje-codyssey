# a2-1: AI 브랜드 아이덴티티 생성기

JSON 브랜드 브리프를 입력받아 OpenAI API로 네이밍, 슬로건, 브랜드 스토리, 컬러 팔레트와 로고 시안을 생성하는 Python 3.10+ CLI 프로그램이다. 텍스트 응답은 구조화 출력으로 검증하고, 생성된 컬러 팔레트와 로고는 PNG로 저장한다.

## 설치 및 API 키 설정

```bash
cd a2-1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`의 `OPENAI_API_KEY` 값을 실제 키로 바꾼다. 키는 코드나 Git에 저장하지 않는다. 셸 환경변수로 설정해도 된다.

```bash
export OPENAI_API_KEY="발급받은_API_키"
```

기본 텍스트 모델은 `gpt-5.4-mini`, 이미지 모델은 `gpt-image-2`다. 계정에서 사용할 수 있는 다른 모델이 필요하면 `OPENAI_TEXT_MODEL`, `OPENAI_IMAGE_MODEL`을 변경할 수 있다. GPT Image 모델 사용에는 계정/조직 상태에 따라 별도 확인이 필요할 수 있다.

## 브리프 형식

필수 필드는 `industry`, `target`, `keywords`다. `tone`, `competitors`, `notes`는 생략할 수 있다.

```json
{
  "industry": "친환경 화장품",
  "target": "20~30대 여성",
  "keywords": ["자연", "순수", "건강"],
  "tone": "따뜻하고 신뢰감 있는",
  "competitors": ["이니스프리", "아로마티카"],
  "notes": "투명한 원료 철학을 강조해 주세요."
}
```

바로 실행할 수 있는 예제는 `brief.json`에 들어 있다.

## 실행

```bash
python brand_generator.py
```

프롬프트에 브리프 파일 경로와 출력 폴더를 입력한다.

```text
🎨 AI 브랜드 아이덴티티 생성기

브리프 파일 경로를 입력하세요: brief.json
출력 폴더 경로를 입력하세요 (엔터 시 ./output):
```

로고는 기본 2개를 생성한다. 3개가 필요하면 `.env`에서 다음처럼 설정한다. 이미지 한 장마다 API 사용량과 비용이 추가된다.

```dotenv
BRAND_LOGO_COUNT=3
```

## 결과 파일

출력 폴더에 다음 파일이 저장된다.

- `brand_result.json`: 입력 브리프, 네이밍 3~5개(한글/영문/의미), 핵심 은유·심볼 논리·시각 모드를 포함한 비주얼 전략, 슬로건 3개, 약 300자 브랜드 스토리, 컬러 정보, 경쟁사 차별화 포인트, 생성 자산 경로와 오류 목록
- `color_palette.png`: 메인 1색과 서브 2~3색을 시각화한 팔레트
- `logo_01.png`, `logo_02.png` (선택 시 `logo_03.png`): 히어로 로고, 구성 원리, 적용 예시, 컬러/시스템을 2×2로 보여 주는 프리미엄 로고 콘셉트 보드

결과 JSON은 각 단계가 끝날 때마다 갱신된다. 따라서 중간 API 호출이 실패해도 앞 단계의 성공 결과는 남고 다음 단계는 계속 실행된다.

## 오류 처리

- 브리프 파일 없음/JSON 오류/필수 필드 누락: 문제 위치를 출력하고 API 호출 전에 종료한다.
- API 키 없음: 설정 방법을 안내하고 `brand_result.json`의 `errors`에 기록한다.
- 인증 실패, 호출 한도, 네트워크 오류, 잘못된 API 응답: 해당 단계 오류를 기록하고 다음 생성 단계를 계속한다.
- 팔레트 이미지 또는 특정 로고 저장 실패: 성공한 다른 텍스트/이미지는 그대로 보존한다.

OpenAI Python SDK는 일시적 연결 오류와 일부 서버 오류를 최대 2회 재시도하며, 프로그램은 단계별 오류를 별도로 처리한다.

## 구현 파이프라인

1. `input()`으로 파일/출력 경로 수집
2. Pydantic으로 JSON 브리프 필드와 타입 검증
3. Responses API 구조화 출력으로 네이밍 → 슬로건 → 스토리 → 팔레트 생성
4. matplotlib로 HEX 컬러 팔레트를 PNG로 렌더링
5. Image API로 전략과 핵심 은유에 연결된 로고 콘셉트 보드 2~3개 생성
6. 단계마다 `brand_result.json` 저장, 오류 발생 시 다음 단계 계속

API 사용 방식은 [OpenAI 구조화 출력 문서](https://developers.openai.com/api/docs/guides/structured-outputs)와 [이미지 생성 문서](https://developers.openai.com/api/docs/guides/image-generation)를 기준으로 작성했다.
