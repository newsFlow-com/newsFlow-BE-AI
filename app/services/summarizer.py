from anthropic import AsyncAnthropic
from app.config import settings

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

_PROMPT = (
    "다음 뉴스 기사를 핵심 내용 3줄로 요약해줘. "
    "각 줄은 '•'로 시작하고 줄바꿈으로 구분해. 설명 없이 요약만 출력해.\n\n"
    "제목: {title}\n\n내용:\n{body}"
)


async def summarize(title: str, content: str | None, summary: str | None) -> str:
    body = (content or summary or "")[:3000]
    message = await _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": _PROMPT.format(title=title, body=body)}],
    )
    return message.content[0].text
