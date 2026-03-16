from pydantic import BaseModel
from typing import Optional, Literal, List


class SearchQuery(BaseModel):
    q: str
    type: str = 'track'
    market: Optional[str] = None
    limit: int = 10
    offset: int = 0
    include_external: Optional[str] = None

class TrackRecommendation(BaseModel):
    track_name: str
    artist_name: str

class PlaylistRecommendation(BaseModel):
    tracks: List[TrackRecommendation]