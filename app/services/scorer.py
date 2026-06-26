import math
from datetime import datetime, timezone


def score_article(
    view_count: int,
    keyword_count: int,
    collected_at: datetime,
) -> float:
    """기사 중요도 복합 스코어 (0~100).

    - 조회수: log 스케일, 최대 40점
    - 키워드 수: 최대 30점
    - 최신성: 수집 후 경과 시간 기준 감쇠, 최대 30점
    """
    view_score = min(math.log1p(view_count) * 5, 40)
    keyword_score = min(keyword_count * 3, 30)

    if collected_at.tzinfo is None:
        collected_at = collected_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - collected_at).total_seconds() / 3600
    recency_score = max(0.0, 30.0 - age_hours * 0.3)

    return round(view_score + keyword_score + recency_score, 2)
