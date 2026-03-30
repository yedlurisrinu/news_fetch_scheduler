from typing import Optional

from pydantic import BaseModel

class Article(BaseModel):
    source: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    link: Optional[str]
    published_at: Optional[str]
    fetched_at: Optional[str]
