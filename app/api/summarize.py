from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article
from app.services.summarizer import summarize

router = APIRouter(prefix="/summarize", tags=["Summarize"])


class SummarizeRequest(BaseModel):
    article_id: str


@router.post("")
async def summarize_article(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Article).where(Article.id == UUID(request.article_id))
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

    ai_summary = await summarize(article.title, article.content, article.summary)
    return {"article_id": request.article_id, "ai_summary": ai_summary}
