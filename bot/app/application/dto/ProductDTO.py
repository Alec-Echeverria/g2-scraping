from typing import Optional
from pydantic import BaseModel, field_validator

class ProductDTO(BaseModel):
    title: str
    vendor: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None
    page: int
    index: int

    @field_validator("vendor", "description", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


    