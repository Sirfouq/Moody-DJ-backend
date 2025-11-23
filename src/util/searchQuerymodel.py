from pydantic import BaseModel
from typing import Optional,Literal


class SearchQuery(BaseModel):
    q: str
    type: Literal['track'] = 'track'
    market: Optional[str] = None
    limit: int = 10
    offset: int = 0
    include_external: Optional[str] = None

