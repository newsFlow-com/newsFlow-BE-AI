from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.recommender import get_recommendations

router = APIRouter(prefix="/recommend", tags=["Recommend"])


@router.get("/{user_id}")
async def recommend(
    user_id: str,
    size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    articles = await get_recommendations(db, user_id, size)
    return {"user_id": user_id, "articles": articles}
