from dependency_injector import containers, providers

from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IScraperService import IScraperService
from app.domain.interfaces.IBrowserManager import IBrowserManager


from app.config.config import Settings, loadJson
from app.application.services.scraper.Scraper import Scraper
from app.application.services.ScraperService import ScraperService
from app.infrastructure.browser.BrowserManager import BrowserManager
from app.infrastructure.filesystem.TempWorkspace import TempWorkspace
from app.infrastructure.browser.FingerprintGenerator import FingerprintGenerator

class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)
    wiring_config = containers.WiringConfiguration(
        modules=["main"]
    )
    
    # Filesystem 
    tempWorkspace = providers.Singleton(
        TempWorkspace,
        basePath = settings.provided.file.tempFolder
    )
    
    # FingerprintGenerator
    fingerprintConfig = providers.Singleton(
        loadJson,
        path=settings.provided.fingerprint.configPath,
    )
    
    fingerprintGenerator = providers.Factory(
        FingerprintGenerator,
        config=fingerprintConfig,
        seed=settings.provided.fingerprint.seed,
        osType = settings.provided.fingerprint.osType,
        regionCode=settings.provided.fingerprint.regionCode,
    )
    
    # Provider manager de browser
    browserManager : providers.Singleton[IBrowserManager] = providers.Singleton(
        BrowserManager,
        proxies = settings.provided.proxy.proxies,
        fingerprintGenerator = fingerprintGenerator,
        binaryLocation = settings.provided.nav.binaryLocation,
        remoteUrl = settings.provided.nav.remoteUrl,
        extraArgs = settings.provided.nav.extraArgs,
    )
    
    
    # Scraper
    scraper : providers.Factory[IScraper] = providers.Factory(
        Scraper,
        browserManager = browserManager,
        url = settings.provided.scraper.url,
    )
    
    # Service 
    scraperService:providers.Singleton[IScraperService] = providers.Singleton(
        ScraperService,
        scraper = scraper,
        tempWorkspace = tempWorkspace,
        persistent = settings.provided.file.persistent,
    )
    