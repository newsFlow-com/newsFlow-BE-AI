from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    original_url = Column(Text)
    language_code = Column(String(10))
    status = Column(String(20))
    view_count = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True))

    article_categories = relationship("ArticleCategory", back_populates="article")


class ArticleCategory(Base):
    __tablename__ = "article_categories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))

    article = relationship("Article", back_populates="article_categories")
    category = relationship("Category")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    slug = Column(String(50))
    name = Column(String(100))


class UserCategory(Base):
    __tablename__ = "user_categories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    preference_weight = Column(Float, default=1.0)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))


class ArticleView(Base):
    __tablename__ = "article_views"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    viewed_at = Column(DateTime(timezone=True))


class ArticleKeyword(Base):
    __tablename__ = "article_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    keyword_id = Column(UUID(as_uuid=True))
    relevance_score = Column(Float, default=0.0)
