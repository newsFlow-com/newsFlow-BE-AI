from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import highlight, recommend, summarize

app = FastAPI(
    title="NewsFlow AI Server",
    description="맞춤 추천 · 핵심 기사 도출 · 기사 요약 AI 엔진",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(highlight.router)
app.include_router(recommend.router)
app.include_router(summarize.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "newsflow-ai"}