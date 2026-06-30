from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article, ArticleCategory, ArticleKeyword, ArticleView, Bookmark, UserCategory
from app.services.scorer import score_article

# 최근 본 기사 기준 기간
VIEW_HISTORY_DAYS = 30
# 추천 후보 기사 기준 기간
CANDIDATE_DAYS = 7
# 카테고리 가중치 — 최근 본 기사와 같은 카테고리일 때 점수에 추가
VIEW_CATEGORY_BOOST = 15.0
# 키워드 가중치 — 최근 본 기사와 같은 키워드가 있을 때 점수에 추가
VIEW_KEYWORD_BOOST = 8.0


async def get_recommendations(
    db: AsyncSession,
    user_id: str,
    size: int = 10,
) -> list[dict]:
    uid = UUID(user_id)

    # 관심 카테고리 조회
    uc_stmt = select(UserCategory).where(UserCategory.user_id == uid)
    uc_result = await db.execute(uc_stmt)
    user_categories = uc_result.scalars().all()

    # 이미 본 기사 ID (최근 VIEW_HISTORY_DAYS일)
    viewed_ids, view_category_weights, view_keyword_weights = await _get_view_history(db, uid)

    # 북마크 기사 ID
    bm_stmt = select(Bookmark.article_id).where(Bookmark.user_id == uid)
    bm_result = await db.execute(bm_stmt)
    bookmarked_ids = {row[0] for row in bm_result}

    # 제외 ID = 이미 본 기사 + 북마크
    excluded_ids = viewed_ids | bookmarked_ids

    if not user_categories:
        return await _get_recent_articles(db, excluded_ids, size)

    category_ids = [uc.category_id for uc in user_categories]
    since = datetime.now(timezone.utc) - timedelta(days=CANDIDATE_DAYS)

    conditions = [
        ArticleCategory.category_id.in_(category_ids),
        Article.status == "active",
        Article.collected_at >= since,
    ]
    if excluded_ids:
        conditions.append(Article.id.not_in(excluded_ids))

    stmt = (
        select(Article)
        .join(ArticleCategory, ArticleCategory.article_id == Article.id)
        .where(and_(*conditions))
        .distinct()
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    if not articles:
        return await _get_recent_articles(db, excluded_ids, size)

    # 기사별 키워드 수 일괄 조회
    keyword_counts = await _get_keyword_counts(db, [a.id for a in articles])

    # 기사별 카테고리/키워드 조회 (가중치 계산용)
    article_category_map = await _get_article_categories(db, [a.id for a in articles])
    article_keyword_map = await _get_article_keywords(db, [a.id for a in articles])

    scored = []
    for article in articles:
        base_score = score_article(
            article.view_count,
            keyword_counts.get(article.id, 0),
            article.collected_at,
        )
        # 최근 열람 카테고리와 겹치는 경우 부스트
        article_cats = article_category_map.get(article.id, set())
        cat_boost = sum(
            VIEW_CATEGORY_BOOST * weight
            for cat_id, weight in view_category_weights.items()
            if cat_id in article_cats
        )
        # 최근 열람 키워드와 겹치는 경우 부스트
        article_kws = article_keyword_map.get(article.id, set())
        kw_boost = sum(
            VIEW_KEYWORD_BOOST * weight
            for kw_id, weight in view_keyword_weights.items()
            if kw_id in article_kws
        )
        scored.append((base_score + cat_boost + kw_boost, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [_to_dict(score, a) for score, a in scored[:size]]


async def _get_view_history(
    db: AsyncSession,
    uid: UUID,
) -> tuple[set, dict, dict]:
    """최근 VIEW_HISTORY_DAYS일 열람 이력 반환.

    Returns:
        viewed_ids: 본 기사 ID 집합
        view_category_weights: {category_id: 정규화된 가중치}
        view_keyword_weights: {keyword_id: 정규화된 가중치}
    """
    since = datetime.now(timezone.utc) - timedelta(days=VIEW_HISTORY_DAYS)
    view_stmt = (
        select(ArticleView)
        .where(and_(ArticleView.user_id == uid, ArticleView.viewed_at >= since))
        .order_by(ArticleView.viewed_at.desc())
    )
    view_result = await db.execute(view_stmt)
    views = view_result.scalars().all()

    if not views:
        return set(), {}, {}

    viewed_ids = {v.article_id for v in views}
    viewed_article_ids = list(viewed_ids)

    # 본 기사들의 카테고리 조회
    cat_stmt = select(ArticleCategory).where(
        ArticleCategory.article_id.in_(viewed_article_ids)
    )
    cat_result = await db.execute(cat_stmt)
    article_cats = cat_result.scalars().all()

    category_counter: Counter = Counter()
    for ac in article_cats:
        category_counter[ac.category_id] += 1

    if category_counter:
        max_count = max(category_counter.values())
        view_category_weights = {c: n / max_count for c, n in category_counter.items()}
    else:
        view_category_weights = {}

    # 본 기사들의 키워드 조회
    kw_stmt = select(ArticleKeyword).where(
        ArticleKeyword.article_id.in_(viewed_article_ids)
    )
    kw_result = await db.execute(kw_stmt)
    article_kws = kw_result.scalars().all()

    keyword_counter: Counter = Counter()
    for ak in article_kws:
        keyword_counter[ak.keyword_id] += 1

    if keyword_counter:
        max_kw = max(keyword_counter.values())
        view_keyword_weights = {k: n / max_kw for k, n in keyword_counter.items()}
    else:
        view_keyword_weights = {}

    return viewed_ids, view_category_weights, view_keyword_weights


async def _get_keyword_counts(db: AsyncSession, article_ids: list) -> dict:
    """기사별 키워드 수 반환."""
    if not article_ids:
        return {}
    stmt = (
        select(ArticleKeyword.article_id, func.count(ArticleKeyword.id).label("cnt"))
        .where(ArticleKeyword.article_id.in_(article_ids))
        .group_by(ArticleKeyword.article_id)
    )
    result = await db.execute(stmt)
    return {row.article_id: row.cnt for row in result}


async def _get_article_categories(db: AsyncSession, article_ids: list) -> dict:
    """기사별 카테고리 ID 집합 반환."""
    if not article_ids:
        return {}
    stmt = select(ArticleCategory).where(ArticleCategory.article_id.in_(article_ids))
    result = await db.execute(stmt)
    category_map: dict = {}
    for ac in result.scalars().all():
        category_map.setdefault(ac.article_id, set()).add(ac.category_id)
    return category_map


async def _get_article_keywords(db: AsyncSession, article_ids: list) -> dict:
    """기사별 키워드 ID 집합 반환."""
    if not article_ids:
        return {}
    stmt = select(ArticleKeyword).where(ArticleKeyword.article_id.in_(article_ids))
    result = await db.execute(stmt)
    keyword_map: dict = {}
    for ak in result.scalars().all():
        keyword_map.setdefault(ak.article_id, set()).add(ak.keyword_id)
    return keyword_map


async def _get_recent_articles(
    db: AsyncSession,
    excluded_ids: set,
    size: int,
) -> list[dict]:
    """관심 카테고리 미설정 또는 후보 없을 때 최근 기사 반환."""
    since = datetime.now(timezone.utc) - timedelta(days=3)
    conditions = [Article.status == "active", Article.collected_at >= since]
    if excluded_ids:
        conditions.append(Article.id.not_in(excluded_ids))

    stmt = (
        select(Article)
        .where(and_(*conditions))
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
