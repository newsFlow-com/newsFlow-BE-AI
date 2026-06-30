import json
import logging

from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

_PROMPT = (
    "다음 뉴스 기사 제목과 요약을 읽고 감성을 분석해줘.\n"
    "경제·시장에 미치는 영향(긍정적·부정적·중립적)을 기준으로 판단해.\n\n"
    "제목: {title}\n"
    "요약: {summary}\n\n"
    "아래 JSON 형식으로만 응답해 (설명 없이):\n"
    '{{\"sentiment\": \"positive|negative|neutral\", \"score\": 0.0~1.0}}\n'
    "score는 감성 강도 (0.0=약함, 1.0=강함)"
)


async def analyze(title: str, summary: str | None) -> dict:
    """기사 감성 분석 → {sentiment, score}."""
    try:
        message = await _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": _PROMPT.format(title=title, summary=summary or "")
            }],
        )
        return json.loads(message.content[0].text.strip())
    except Exception as e:
        logger.warning("감성 분석 실패 (title=%s): %s", title[:30], e)
        return {"sentiment": "neutral", "score": 0.5}
