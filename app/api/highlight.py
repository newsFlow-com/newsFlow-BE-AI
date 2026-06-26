from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article
from app.services.scorer import score_article
from app.services.summarizer import summarize as ai_summarize

router = APIRouter(prefix="/highlight", tags=["Highlight"])


async def _fetch_top_articles(
    db: AsyncSession,
    since: datetime,
    until: datetime,
    top_n: int,
    with_summary: bool,
) -> list[dict]:
    stmt = select(Article).where(
        and_(
            Article.status == "active",
            Article.collected_at >= since,
            Article.collected_at < until,
        )
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    ranked = sorted(
        [(score_article(a.view_count, 0, a.collected_at), a) for a in articles],
        key=lambda x: x[0],
        reverse=True,
    )[:top_n]

    output = []
    for score, a in ranked:
        item = {
            "article_id": str(a.id),
            "title": a.title,
            "summary": a.summary,
            "original_url": a.original_url,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "score": score,
            "ai_summary": None,
        }
        if with_summary:
            item["ai_summary"] = await ai_summarize(a.title, a.content, a.summary)
        output.append(item)

    return output


@router.get("/daily")
async def daily_highlight(
    target_date: date = Query(default=None, description="기준 날짜 (기본: 어제)"),
    top_n: int = Query(default=5, ge=1, le=20),
    with_summary: bool = Query(default=False, description="Claude 3줄 요약 포함"),
    db: AsyncSession = Depends(get_db),
):
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    since = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    until = since + timedelta(days=1)
    articles = await _fetch_top_articles(db, since, until, top_n, with_summary)
    return {"date": str(target_date), "articles": articles}


@router.get("/monthly")
async def monthly_highlight(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    top_n: int = Query(default=5, ge=1, le=20),
    with_summary: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    since = datetime(year, month, 1, tzinfo=timezone.utc)
    until = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 \
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    articles = await _fetch_top_articles(db, since, until, top_n, with_summary)
    return {"year": year, "month": month, "articles": articles}


@router.get("/yearly")
async def yearly_highlight(
    year: int = Query(default=None),
    top_n: int = Query(default=10, ge=1, le=30),
    with_summary: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    year = year or now.year
    since = datetime(year, 1, 1, tzinfo=timezone.utc)
    until = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    articles = await _fetch_top_articles(db, since, until, top_n, with_summary)
    return {"year": year, "articles": articles}
