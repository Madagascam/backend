from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAEnum

from app.core.analysis_base.analysis_interface import StrategyType


class Base(DeclarativeBase, AsyncAttrs):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )


class UserRole(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLAEnum(UserRole), default=UserRole.USER)

    # Relationships
    games: Mapped[List["Game"]] = relationship(back_populates="user")
    tasks: Mapped[List["Task"]] = relationship(back_populates="user")


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    event: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[datetime] = mapped_column()
    white_player: Mapped[str] = mapped_column(String(255))
    black_player: Mapped[str] = mapped_column(String(255))
    pgn_data: Mapped[str] = mapped_column(Text)

    # Relationships
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[Optional["User"]] = relationship(back_populates="games")

    highlights: Mapped[List["Highlight"]] = relationship(back_populates="game")
    videos: Mapped[List["Video"]] = relationship(back_populates="game")
    tasks: Mapped[List["Task"]] = relationship(back_populates="game", cascade="all, delete-orphan")


class Highlight(Base, TimestampMixin):
    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_move: Mapped[str] = mapped_column(String(5))
    end_move: Mapped[str] = mapped_column(String(5))
    description: Mapped[str] = mapped_column(Text)
    detected_by: Mapped[str] = mapped_column(String(255), default="AI")

    # Relationships
    game_id: Mapped[Optional[int]] = mapped_column(ForeignKey("games.id"), nullable=True)
    game: Mapped[Optional["Game"]] = relationship(back_populates="highlights")

    video_segment: Mapped[Optional["VideoSegment"]] = relationship(back_populates="highlight", uselist=False)


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_video_url: Mapped[str] = mapped_column(String(255))
    processed_video_url: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))

    # Relationships - removed unique constraint for one-to-many
    game_id: Mapped[Optional[int]] = mapped_column(ForeignKey("games.id"), nullable=True)
    game: Mapped[Optional["Game"]] = relationship(back_populates="videos")

    segments: Mapped[List["VideoSegment"]] = relationship(back_populates="video")


class VideoSegment(Base, TimestampMixin):
    __tablename__ = "video_segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_time: Mapped[int] = mapped_column(Integer)
    end_time: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(String(255))

    # Relationships
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    video: Mapped[Optional["Video"]] = relationship(back_populates="segments")

    # One-to-one relationship with highlight (using unique constraint)
    highlight_id: Mapped[Optional[int]] = mapped_column(ForeignKey("highlights.id"), unique=True, nullable=True)
    highlight: Mapped[Optional["Highlight"]] = relationship(back_populates="video_segment")


class TaskType(str, Enum):
    GAME_ANALYSIS = "game_analysis"
    VIDEO_PROCESSING = "video_processing"
    HIGHLIGHT_DETECTION = "highlight_detection"
    VIDEO_EFFECTS = "video_effects"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[TaskType] = mapped_column(SQLAEnum(TaskType))
    status: Mapped[TaskStatus] = mapped_column(SQLAEnum(TaskStatus), default=TaskStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strategy_type: Mapped[Optional[StrategyType]] = mapped_column(SQLAEnum(StrategyType), nullable=True,
                                                                  default=StrategyType.ANALYTICS)

    # Relationships
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    game: Mapped["Game"] = relationship(back_populates="tasks")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="tasks")

    # Optional commented fields from the original model
    # video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    # highlight_id: Mapped[Optional[int]] = mapped_column(ForeignKey("highlights.id"), nullable=True)


class LogType(int, Enum):
    system = 0
    exceptions = 1
    user = 2


class Log(Base, TimestampMixin):
    __tablename__ = 'logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    log_type: Mapped[LogType] = mapped_column(SQLAEnum(LogType))
    text: Mapped[str]
