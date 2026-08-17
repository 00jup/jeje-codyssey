import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

logging.getLogger("google_genai.models").setLevel(logging.ERROR)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def parse_args():
    parser = argparse.ArgumentParser(
        prog="travel_planner.py",
        description="LLM(Gemini) + 지도 API(Kakao Local)를 조합한 국내 여행지 추천 프로그램",
    )
    parser.add_argument("--date", required=True, help='여행 날짜, 형식: "YYYY-MM-DD" (예: 2026-03-15)')
    args = parser.parse_args()
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.print_usage(sys.stderr)
        print('오류: --date 값은 "YYYY-MM-DD" 형식이어야 합니다. 예) --date "2026-03-15"', file=sys.stderr)
        sys.exit(1)
    return args.date


def load_api_keys():
    load_dotenv(BASE_DIR / ".env")
    gemini_key = os.getenv("GEMINI_API_KEY")
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    missing = [k for k, v in (("GEMINI_API_KEY", gemini_key), ("KAKAO_REST_API_KEY", kakao_key)) if not v]
    if missing:
        print(f"오류: 다음 API 키가 설정되지 않았습니다: {', '.join(missing)}")
        print("b2-2/.env 파일을 만들고 아래처럼 값을 채워주세요 (b2-2/.env.example 참고):")
        for k in missing:
            print(f'  {k}="YOUR_KEY"')
        print("자세한 발급 방법은 b2-2/README.md 를 참고하세요.")
        sys.exit(1)
    return gemini_key, kakao_key


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text[: text.rfind("```")] if "```" in text else text
    return text.strip()


def get_primary_recommendation(client, model, date_str, errors):
    schema_hint = (
        '{"recommended_city": "string", "weather": "string", '
        '"events": ["string", "..."], "reason": "string"}'
    )
    prompt = (
        f"당신은 한국 국내 여행 전문가입니다. 사용자가 {date_str}에 여행을 떠납니다.\n"
        f"이 시기에 여행하기 좋은 국내 도시/지역 1곳을 추천하고, 아래 JSON 스키마로만 응답하세요.\n"
        f"다른 설명 문구나 코드블록 없이 JSON 객체 하나만 출력하세요.\n\n"
        f"스키마: {schema_hint}\n"
        f"- events는 해당 시기 행사/축제 후보 1~3개\n"
        f"- reason은 추천 근거 2~4문장"
    )
    retry_suffix = (
        "\n\n이전 응답은 올바른 JSON이 아니었습니다. "
        "recommended_city, weather, events, reason 4개 키만 포함한 "
        "순수 JSON 객체 하나만 다시 출력하세요. 설명이나 코드블록은 포함하지 마세요."
    )

    for attempt in range(2):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt if attempt == 0 else prompt + retry_suffix,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(strip_code_fence(resp.text))
            required_keys = {"recommended_city", "weather", "events", "reason"}
            if not required_keys.issubset(data.keys()):
                raise ValueError(f"필수 키 누락: {required_keys - data.keys()}")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            errors.append({"step": "primary_recommendation", "type": "JSON_PARSE_ERROR", "message": str(e)})
        except Exception as e:
            errors.append({"step": "primary_recommendation", "type": "LLM_ERROR", "message": str(e)})
            break
    return None


def search_restaurants(kakao_key, city, errors, size=5):
    try:
        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/keyword.json",
            headers={"Authorization": f"KakaoAK {kakao_key}"},
            params={"query": f"{city} 맛집", "size": size},
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        errors.append({"step": "place_search", "type": "NETWORK_ERROR", "message": str(e)})
        return []

    if resp.status_code in (401, 403):
        errors.append({"step": "place_search", "type": "AUTH_ERROR", "message": f"HTTP {resp.status_code}"})
        return []
    if resp.status_code != 200:
        errors.append({"step": "place_search", "type": "HTTP_ERROR", "message": f"HTTP {resp.status_code}"})
        return []

    documents = resp.json().get("documents", [])
    if not documents:
        errors.append({"step": "place_search", "type": "EMPTY_RESULT", "message": f"0 results for query={city} 맛집"})
        return []

    return [
        {
            "name": d.get("place_name"),
            "address": d.get("road_address_name") or d.get("address_name"),
            "category": d.get("category_name"),
            "url": d.get("place_url"),
            "x": d.get("x"),
            "y": d.get("y"),
        }
        for d in documents
    ]


def render_errors_section(errors):
    if not errors:
        return "\n\n## 오류 요약(errors)\n- 없음\n"
    lines = [f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors]
    return "\n\n## 오류 요약(errors)\n" + "\n".join(lines) + "\n"


def render_fallback_report(date_str, primary, restaurants_text, events_text):
    return f"""# {date_str} 국내 여행 추천 리포트

## 추천 지역
{primary.get('recommended_city')}

## 추천 이유
{primary.get('reason')}

## 날씨 요약
{primary.get('weather')}

## 행사/축제
{events_text}

## 맛집 추천
{restaurants_text}

## 1일 일정 제안
- 오전: 추천 지역의 대표 명소를 둘러봅니다.
- 오후: 인근 카페 또는 자연 명소에서 휴식을 취합니다.
- 저녁: 맛집 리스트를 참고해 현지 음식을 즐깁니다."""


def generate_final_report(client, model, date_str, primary, restaurants, errors):
    events_text = ", ".join(primary.get("events") or []) or "없음"
    if restaurants:
        restaurants_text = "\n".join(
            f"- {r['name']} | {r['address']} | {r.get('category') or '-'} | {r.get('url') or '-'}"
            for r in restaurants
        )
    else:
        restaurants_text = "없음 (장소 검색 결과 0건)"

    prompt = f"""아래 정보를 바탕으로 한국어 마크다운 여행 리포트를 작성하세요.

[1차 추천 정보]
- 추천 지역: {primary.get('recommended_city')}
- 날씨 요약: {primary.get('weather')}
- 행사/축제: {events_text}
- 추천 이유: {primary.get('reason')}

[맛집 목록]
{restaurants_text}

아래 마크다운 형식(제목 레벨과 순서)을 반드시 그대로 따르되, '오류 요약' 섹션은 작성하지 마세요(별도로 추가됩니다):

# {date_str} 국내 여행 추천 리포트

## 추천 지역

## 추천 이유

## 날씨 요약

## 행사/축제

## 맛집 추천

## 1일 일정 제안

각 섹션을 위 정보로 자연스럽게 채우세요. 맛집 목록이 "없음"이면 맛집 추천 섹션에 "데이터 없음 (장소 검색 결과 0건)"이라고만 적으세요. 1일 일정 제안은 오전/오후/저녁으로 나눠 2~3문장씩 제안하세요."""

    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        report_body = strip_code_fence(resp.text)
    except Exception as e:
        errors.append({"step": "report_generation", "type": "LLM_ERROR", "message": str(e)})
        report_body = render_fallback_report(date_str, primary, restaurants_text, events_text)

    return report_body.rstrip() + render_errors_section(errors)


def load_cached_data(date_str):
    raw_path = RESULTS_DIR / f"{date_str}_raw_data.json"
    if not raw_path.exists():
        return None
    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not data.get("primary_recommendation"):
        return None
    return data


def save_results(date_str, primary, restaurants, errors, report_md=None):
    RESULTS_DIR.mkdir(exist_ok=True)
    raw = {
        "date": date_str,
        "primary_recommendation": primary,
        "restaurants": restaurants,
        "errors": errors,
    }
    raw_path = RESULTS_DIR / f"{date_str}_raw_data.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = None
    if report_md is not None:
        report_path = RESULTS_DIR / f"{date_str}_travel_plan.md"
        report_path.write_text(report_md, encoding="utf-8")
    return raw_path, report_path


def main():
    date_str = parse_args()
    gemini_key, kakao_key = load_api_keys()
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    client = genai.Client(api_key=gemini_key)
    errors = []

    cached = load_cached_data(date_str)
    if cached:
        print(f"캐시된 원본 데이터 발견({date_str}) - API 호출을 건너뛰고 재사용합니다.")
        primary = cached["primary_recommendation"]
        restaurants = cached.get("restaurants", [])
        errors = cached.get("errors", [])
        print(f'    - recommended_city: "{primary.get("recommended_city")}"')
    else:
        print("[1/3] 1차 추천 생성 중(LLM)...")
        primary = get_primary_recommendation(client, model, date_str, errors)
        if primary is None:
            print("오류: 1차 추천 생성에 실패했습니다 (LLM JSON 파싱/호출 오류).")
            save_results(date_str, None, [], errors)
            sys.exit(1)
        print(f'    - recommended_city: "{primary.get("recommended_city")}"')

        print("[2/3] 맛집 검색 중(지도/장소 API)...")
        restaurants = search_restaurants(kakao_key, primary.get("recommended_city", ""), errors)
        if restaurants:
            print(f"    - 맛집 {len(restaurants)}곳 검색 완료")
        else:
            print("    - 검색 결과 0건(데이터 없음 처리 후 다음 단계로 진행)")

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report_md = generate_final_report(client, model, date_str, primary, restaurants, errors)
    print("    - 리포트 생성 완료")

    _, report_path = save_results(date_str, primary, restaurants, errors, report_md)
    print(f"\n완료! {report_path.relative_to(BASE_DIR)} 를 확인하세요.")


if __name__ == "__main__":
    main()
