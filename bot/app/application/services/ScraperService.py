import uuid
import json
import logging
from pathlib import Path
from datetime import datetime

from app.domain.interfaces.IScraper import IScraper
from app.application.dto.ProductDTO import ProductDTO
from app.infrastructure.filesystem.Workspace import Workspace
from app.domain.interfaces.IScraperService import IScraperService

class ScraperService(IScraperService):
    def __init__(self, scraper:IScraper, persistent:bool, workspace:Workspace):
        self.scraper = scraper
        self.workspace = workspace
        self.persistent = persistent

    async def process(self)-> ProductDTO:
        try:
            logging.info(f"~ Inicia proceso")
            folderName = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-{uuid.uuid4().hex[:8]}"
            
            with self.workspace.useFolder(folderName,  self.persistent) as outputDir:
                rawData = await self.scraper.scraping()
                if rawData:
                    data = [ProductDTO(**item) for item in rawData]
                    
                    # Convertir a JSON serializable
                    jsonData = [item.model_dump() for item in data]

                    #  Guardar archivo
                    filePath: Path = outputDir / f"products_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

                    with open(filePath, "w", encoding="utf-8") as f:
                        json.dump(jsonData, f, ensure_ascii=False, indent=2)

                    logging.info(f"Archivo generado en: {filePath}")
                    
            logging.info(f"~ Finaliza proceso")
            
        except Exception as e:
            logging.exception(f"🔴 Error procesando mensaje {e}")
            raise

        

