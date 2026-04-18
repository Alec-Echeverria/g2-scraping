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
    pages:int = Field(..., alias="PAGES")
    url: str  = Field(..., alias="BASE_URL")
    retries:int = Field(..., alias="RETRIES")
    attemps:int = Field(..., alias="ATTEMPS")
        
class NavigatorSettings(EnvConfig):
    binaryLocation: str  = Field(..., alias="BINARY_LOCATION")
    remoteUrl: Optional[str] = Field(..., alias="REMOTE_URL")
    extraArgs: List[str] = Field(default_factory=list, alias="EXTRA_ARGS")
    
    @field_validator("remoteUrl", mode="before")
    @classmethod
    def parse_remote_url(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v

    @field_validator("extraArgs", mode="before")
    @classmethod
    def parse_extra_args(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

class FingerprintSettings(EnvConfig):
    seed: str = Field(..., alias="SEED")
    osType:str = Field(..., alias="OS_TYPE")
    regionCode:str = Field(..., alias="REGION_CODE")
    configPath: Path = Field(..., alias="CONFIG_PATH")

class Settings(EnvConfig):
    file: FileSettings = FileSettings()
    proxy: proxiesSettings = proxiesSettings()
    scraper:ScraperSettings = ScraperSettings()
    nav: NavigatorSettings = NavigatorSettings()
    fingerprint: FingerprintSettings = FingerprintSettings()
    
def loadConfig() -> Settings:
    return Settings()

def loadJson(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Fingerprint config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
