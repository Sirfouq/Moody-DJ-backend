from pydantic import BaseModel
from typing import Optional,Literal

class SpotifyResponseData(BaseModel):
    name: str
    artists: list[str]
    uri : str
    album_image_url : str
    duration_ms : int
