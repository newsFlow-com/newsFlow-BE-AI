# newsFlow-BE-AI

> NewsFlow 플랫폼의 AI 추천 및 분석 엔진 레포지토리입니다.  
> 사용자 맞춤형 기사 추천, 기사 중요도 스코어링, 날짜·월·연 단위 핵심 기사 도출을 담당합니다.  
> `newsFlow-BE-API(Spring Boot)`로부터 요청을 받아 결과만 반환하는 내부 서비스입니다.

---

## 📌 사용 목적

- `newsFlow-BE-API`로부터 추천 요청을 수신하여 **사용자 맞춤형 기사 추천** 결과 반환
- 날짜별·월별·연별 기사를 분석하여 **가장 중요한 기사를 자동 도출**
- 기사별 중요도 스코어 산출 (조회수, 공유수, 체류 시간, 키워드 빈도 등 복합 지표)
- LLM(Claude API)을 활용한 기사 요약 및 키워드 추출
- 집계·캐싱·트래픽 처리는 `newsFlow-BE-API`에 위임, AI 연산에만 집중

---

## 🛠 기술 스택

| 분류 | 기술 | 용도 |
|------|------|------|
| **Language** | Python 3.11 | AI/ML 생태계 활용을 위한 메인 언어 |
| **Framework** | FastAPI | 비동기 고성능 API 서버, 자동 Swagger 문서 |
| **LLM 연동** | Anthropic Claude API | 기사 요약, 핵심 기사 선별, 키워드 추출 |
| **ML 프레임워크** | scikit-learn | 콘텐츠 기반 추천, TF-IDF 유사도 계산 |
| **NLP** | kiwipiepy | 한국어 형태소 분석, 키워드 추출 |
| **키워드 추출** | KeyBERT + kiwipiepy | 의미 기반 핵심 키워드 도출 |
| **임베딩** | sentence-transformers | 기사 의미 기반 벡터화 |
| **벡터 유사도 검색** | pgvector (PostgreSQL 확장) | 유사 기사 추천 |
| **비동기 작업 큐** | Celery + Redis | 배치 추천 연산 비동기 처리 |
| **정기 스케줄 실행** | APScheduler | 일별·월별·연별 핵심 기사 도출 자동 실행 |
| **DB 연결** | SQLAlchemy + asyncpg | 비동기 PostgreSQL 연결 |
| **데이터 검증** | Pydantic v2 | 요청·응답 데이터 스키마 검증 |
| **HTTP 클라이언트** | httpx | BE-API 서버와의 내부 통신 |
| **테스트** | pytest + pytest-asyncio | 비동기 단위·통합 테스트 |
| **컨테이너** | Docker + docker-compose | 환경 통일 및 배포 |

---

## 📁 주요 디렉토리 구조

```
newsFlow-BE-AI/
├── app/
│   ├── api/
│   │   ├── recommend.py        # 맞춤 추천 API 엔드포인트
│   │   └── highlight.py        # 핵심 기사 도출 API 엔드포인트
│   ├── services/
│   │   ├── recommender.py      # 추천 알고리즘 (콘텐츠 기반 + 협업 필터링)
│   │   ├── scorer.py           # 기사 중요도 스코어링
│   │   ├── summarizer.py       # Claude API 기반 기사 요약
│   │   └── keyword_extractor.py# 한국어 키워드 추출 및 트렌드 분석
│   ├── models/                 # ML 모델 정의 및 로딩
│   ├── tasks/                  # Celery 비동기 태스크
│   └── scheduler/              # APScheduler 정기 실행 설정
├── tests/
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

---

## ✅ 핵심 기능 목록

- [ ] 사용자별 맞춤 기사 추천 (콘텐츠 기반 + 협업 필터링)
- [ ] **날짜별 핵심 기사 도출** (일간 Top N 선별)
- [ ] **월별·연별 가장 중요한 기사 선별**
- [ ] 기사 중요도 스코어링 (조회수, 반응, 노출 지표 복합)
- [ ] Claude API를 활용한 기사 3줄 요약 생성
- [ ] 한국어 키워드 추출 및 트렌드 집계
- [ ] 기사 임베딩 기반 유사 기사 추천
- [ ] 신규 기사 수집 시 자동 스코어링 파이프라인 (Celery)

---

## 🔗 연관 레포지토리

| 레포지토리 | 역할 |
|------------|------|
| `newsFlow-BE-API` | 추천 요청 송신 및 결과 수신 후 FE로 중계 (Spring Boot) |
| `newsFlow-BE-DATA` | 기사 원천 데이터 및 메타데이터 공급 |
