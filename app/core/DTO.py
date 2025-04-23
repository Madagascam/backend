from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app import UserRole
from app.core import StrategyType


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class UserCreateSchema(BaseModel):
    username: str
    password: str


class UserLoginSchema(BaseModel):
    username: str
    password: str


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

    class Config:
        from_attributes = True


class UserResponseSchema(BaseModel):
    id: int
    username: str
    role: UserRole

    class Config:
        from_attributes = True


class GameCreateSchema(BaseModel):
    title: str
    event: Optional[str] = None
    white_player: Optional[str] = None
    black_player: Optional[str] = None


class GameResponseSchema(BaseModel):
    id: int
    title: str
    event: Optional[str] = None
    date: datetime
    white_player: str
    black_player: str
    pgn_data: str

    class Config:
        from_attributes = True


class AnalysisResponseSchema(BaseModel):
    id: int
    status: str

    class Config:
        from_attributes = True


class HighlightResponseSchema(BaseModel):
    id: int
    start_move: str
    end_move: str
    description: str
    detected_by: str

    class Config:
        from_attributes = True


class AnalysisResultResponseSchema(BaseModel):
    pgn_data: str
    highlights: List[HighlightResponseSchema]


class GameWithHighlightsResponseSchema(BaseModel):
    game: GameResponseSchema
    highlights: List[HighlightResponseSchema]


class VideoSegmentResponseSchema(BaseModel):
    id: int
    start_move: int
    end_move: int


class AnalysisRequest(BaseModel):
    strategy_type: StrategyType = StrategyType.ANALYTICS
