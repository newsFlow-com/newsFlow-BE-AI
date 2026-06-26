from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article, ArticleCategory, UserCategory, Bookmark
from app.services.scorer import score_article


async def get_recommendations(
    db: AsyncSession,
    user_id: str,
    size: int = 10,
) -> list[dict]:
    uid = UUID(user_id)

    # 관심 카테고리 조회
    stmt = select(UserCategory).where(UserCategory.user_id == uid)
    result = await db.execute(stmt)
    user_categories = result.scalars().all()

    if not user_categories:
        return await _get_recent_articles(db, size)

    category_ids = [uc.category_id for uc in user_categories]

    # 북마크 기사 ID 조회
    bm_stmt = select(Bookmark.article_id).where(Bookmark.user_id == uid)
    bm_result = await db.execute(bm_stmt)
    bookmarked_ids = {row[0] for row in bm_result}

    since = datetime.now(timezone.utc) - timedelta(days=7)

    conditions = [
        ArticleCategory.category_id.in_(category_ids),
        Article.status == "active",
        Article.collected_at >= since,
    ]
    if bookmarked_ids:
        conditions.append(Article.id.not_in(bookmarked_ids))

    stmt = (
        select(Article)
        .join(ArticleCategory, ArticleCategory.article_id == Article.id)
        .where(and_(*conditions))
        .distinct()
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    scored = sorted(
        [(score_article(a.view_count, 0, a.collected_at), a) for a in articles],
        key=lambda x: x[0],
        reverse=True,
    )

    return [_to_dict(score, a) for score, a in scored[:size]]


async def _get_recent_articles(db: AsyncSession, size: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=3)
    stmt = (
        select(Article)
        .where(and_(Article.status == "active", Article.collected_at >= since))
        .order_by(Article.collected_at.desc())
        .limit(size)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return [_to_dict(0.0, a) for a in articles]


def _to_dict(score: float, article: Article) -> dict:
    return {
        "article_id": str(article.id),
        "title": article.title,
        "summary": article.summary,
        "original_url": article.original_url,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "score": score,
    }
