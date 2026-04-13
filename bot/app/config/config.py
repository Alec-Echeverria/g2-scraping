import json
from pathlib import Path
from pydantic import Field,field_validator
from typing import List, Optional

from app.config.base import EnvConfig

class FileSettings(EnvConfig):
    tempFolder: Path  = Field(..., alias="FOLDER")
    persistent: bool  = Field(..., alias="PERSISTENT")

class proxiesSettings(EnvConfig):
    proxies: List[Optional[str]] = Field(default_factory=list, alias="PROXIES")

    @field_validator("proxies", mode="before")
    @classmethod
    def parse_proxies(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

class ScraperSettings(EnvConfig):
    url: str  = Field(..., alias="BASE_URL")
    attemps:int = Field(..., alias="ATTEMPS")

class Settings(EnvConfig):
    file: FileSettings = FileSettings()
    proxy: proxiesSettings = proxiesSettings()
    scraper:ScraperSettings = ScraperSettings()
    
def loadConfig() -> Settings:
    return Settings()