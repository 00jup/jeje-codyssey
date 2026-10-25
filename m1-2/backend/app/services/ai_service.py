import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from openai import OpenAI
from app.config import settings
from app.models.data import DataSummary

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        kwargs = {"api_key": self.api_key}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.client = OpenAI(**kwargs) if self.api_key else None

    def build_system_prompt(self, summary: DataSummary) -> str:
        """
        데이터 요약 정보를 주입하여 시스템 프롬프트를 구성합니다 (컨텍스트 주입).
        """
        prompt = f"""당신은 스마트스토어 점주님을 위한 전문 'AI 매출 분석 비서'입니다.
실제 축적된 매장 시계열 매출 데이터 요약 정보를 기반으로 친절하고 명확하며 비즈니스 인사이트가 담긴 맞춤형 답변을 제공하세요.

[현재 매장 매출 데이터 요약]
- 분석 기간: {summary.period}
- 기록된 영업일: 총 {summary.count}일
- 누적 총 매출: {summary.metrics.total:,}원
- 일평균 매출: {summary.metrics.average:,}원
- 역대 최고 매출: {summary.metrics.max:,}원 ({summary.metrics.max_date})
- 역대 최저 매출: {summary.metrics.min:,}원 ({summary.metrics.min_date})
- 최근 매출 트렌드: {summary.trend}

[답변 가이드라인]
1. 반드시 위 요약 데이터를 사실(Fact)로 삼아 근거를 명확히 들어 답변하세요.
2. 금액은 읽기 편하게 만원 단위(예: 620만원, 약 185만원) 또는 콤마 표기를 병행하세요.
3. 점주님의 질문에 대해 단순 숫자 나열에 그치지 않고, 트렌드에 따른 격려나 실질적인 영업 조언(재고, 프로모션, 주말 대비 등)을 덧붙이세요.
4. 요약에 없는 가상의 수치를 지어내지 말고, 현재 기록된 통계와 기간 내 최고/최저/평균 실적을 중심으로 설명하세요.
"""
        return prompt

    def generate_chat_response(
        self,
        user_message: str,
        summary: DataSummary,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        컨텍스트가 주입된 시스템 프롬프트와 함께 GPT API를 호출합니다.
        """
        system_prompt = self.build_system_prompt(summary)

        # API 키가 설정되지 않은 경우 Fallback 응답
        if not self.client or not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_openai"):
            return self._mock_response(user_message, summary)

        messages = [{"role": "system", "content": system_prompt}]

        # 최근 대화 히스토리 (최대 최근 6턴)
        if chat_history:
            recent_turns = chat_history[-6:]
            for turn in recent_turns:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            reply = response.choices[0].message.content.strip()
            return reply
        except Exception as e:
            print(f"[AIService] OpenAI API call failed: {e}")
            return f"죄송합니다. OpenAI API 호출 중 오류가 발생했습니다: {str(e)}\n\n(참고: .env의 OPENAI_API_KEY 및 잔여 크레딧을 확인해주세요.)"

    def _mock_response(self, user_message: str, summary: DataSummary) -> str:
        """OpenAI API 키가 없을 때 제공되는 친절한 모의 응답 (개발/테스트용)"""
        m = summary.metrics
        msg = user_message.lower()

        if "실적" in msg or "매출" in msg or "얼마" in msg:
            return (
                f"[개발 모드 안내: .env에 OPENAI_API_KEY를 넣으시면 실제 GPT가 답변합니다]\n\n"
                f"현재까지 기록된 총 {summary.count}일간의 누적 매출은 약 {m.total:,}원이며, "
                f"일평균 매출은 약 {m.average:,}원입니다. "
                f"최근 트렌드는 '{summary.trend}' 상태를 보이고 있어요! 🚀"
            )
        elif "최고" in msg or "잘" in msg or "가장" in msg:
            return (
                f"[개발 모드 안내: .env에 OPENAI_API_KEY를 넣으시면 실제 GPT가 답변합니다]\n\n"
                f"가장 실적이 좋았던 날은 {m.max_date}로, 약 {m.max:,}원의 최고 매출을 기록했습니다! 🎉"
            )
        elif "최저" in msg or "안좋" in msg or "적" in msg:
            return (
                f"[개발 모드 안내: .env에 OPENAI_API_KEY를 넣으시면 실제 GPT가 답변합니다]\n\n"
                f"가장 매출이 낮았던 날은 {m.min_date}로, 약 {m.min:,}원이었습니다."
            )
        else:
            return (
                f"[개발 모드 안내: .env에 OPENAI_API_KEY를 넣으시면 실제 GPT가 답변합니다]\n\n"
                f"점주님, 현재 매장의 데이터 분석 기간은 {summary.period} (총 {summary.count}개 데이터)입니다.\n"
                f"- 일평균 매출: {m.average:,}원\n"
                f"- 최고 매출: {m.max:,}원 ({m.max_date})\n"
                f"- 최근 트렌드: {summary.trend}\n\n"
                f"궁금하신 세부 실적이나 트렌드에 대해 언제든 물어보세요!"
            )

ai_service = AIService()
