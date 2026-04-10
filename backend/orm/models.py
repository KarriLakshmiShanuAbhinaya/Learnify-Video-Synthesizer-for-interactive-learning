from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quiz_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiz_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_favorite: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    performance_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
