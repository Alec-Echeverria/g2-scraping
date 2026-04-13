from abc import ABC, abstractmethod

class IScraper(ABC):
    
    @abstractmethod
    async def scraping( proceeding:str):
        ...
