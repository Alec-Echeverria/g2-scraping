from abc import ABC, abstractmethod

class IBrowserManager(ABC):
    
    @property
    @abstractmethod
    def isStarted(self) -> bool:
        ...  
    
    @abstractmethod
    async def restart(self) -> None:
        ...
    
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def getBrowser(self) -> None:
        ...
    
    @abstractmethod
    async def close(self) -> None:
        ...
