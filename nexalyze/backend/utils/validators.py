from pydantic import BaseModel, validator
from typing import Optional, List, Any
import re

class CompanyData(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None

    @validator('website')
    def validate_website(cls, v):
        if v and not re.match(r'^https?://', v):
            v = f'https://{v}'
        return v

    @validator('founded_year')
    def validate_founded_year(cls, v):
        if v and (v < 1800 or v > 2030):
            raise ValueError('Founded year must be reasonable')
        return v

class ResearchQuery(BaseModel):
    query: str
    filters: Optional[dict] = None
    limit: Optional[int] = 10

    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Query must be at least 3 characters')
        return v.strip()
