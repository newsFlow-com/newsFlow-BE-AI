"""
tests/test_sentiment_analyzer.py
감성 분석 서비스 — Claude 응답 mock 검증
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.sentiment_analyzer import analyze


class TestSentimentAnalyzer:

    @pytest.mark.asyncio
    async def test_positive_감성_반환(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"sentiment": "positive", "score": 0.85}')]

        with patch("app.services.sentiment_analyzer._client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await analyze("삼성 역대 최대 실적", "영업이익 10조 돌파")

        assert result["sentiment"] == "positive"
        assert result["score"] == 0.85

    @pytest.mark.asyncio
    async def test_negative_감성_반환(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"sentiment": "negative", "score": 0.72}')]

        with patch("app.services.sentiment_analyzer._client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await analyze("주가 폭락", "코스피 급락")

        assert result["sentiment"] == "negative"
        assert result["score"] == 0.72

    @pytest.mark.asyncio
    async def test_claude_오류시_neutral_기본값_반환(self):
        with patch("app.services.sentiment_analyzer._client") as mock_client:
            mock_client.messages.create = AsyncMock(side_effect=Exception("API 오류"))
            result = await analyze("테스트 기사", None)

        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5

    @pytest.mark.asyncio
    async def test_잘못된_json_응답시_neutral_반환(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="올바른 JSON이 아닙니다")]

        with patch("app.services.sentiment_analyzer._client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await analyze("테스트", "요약")

        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5

    @pytest.mark.asyncio
    async def test_summary_없이_title만으로_분석(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"sentiment": "neutral", "score": 0.5}')]

        with patch("app.services.sentiment_analyzer._client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await analyze("중립적 뉴스", None)

        assert "sentiment" in result
        assert "score" in result
