from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class SearchQuery(BaseModel):
    q: str
    type: str = 'track'
    market: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=10)
    offset: int = 0
    include_external: Optional[str] = None

class TrackRecommendation(BaseModel):
    track_name: str
    artist_name: str

class PlaylistRecommendation(BaseModel):
    tracks: List[TrackRecommendation]