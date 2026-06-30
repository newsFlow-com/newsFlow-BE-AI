from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article
from app.services.sentiment_analyzer import analyze

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


class SentimentRequest(BaseModel):
    article_id: str


@router.post("")
async def sentiment_analysis(
    request: SentimentRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Article).where(Article.id == UUID(request.article_id))
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

    result = await analyze(article.title, article.summary)
    return {
        "article_id": request.article_id,
        "sentiment": result.get("sentiment", "neutral"),
        "score": result.get("score", 0.5),
    }
