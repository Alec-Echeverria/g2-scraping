import logging
import asyncio

from app.config.config import loadConfig
from app.dependencies.Dependencies import Dependencies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logging.getLogger("pydoll").setLevel(logging.WARNING)


async def run():
    config = loadConfig()

    dependency = Dependencies()
    dependency.settings.override(config)
    
    attemps = dependency.settings.provided.scraper.attemps()
    
    browser = dependency.browserManager()
    scraperService = dependency.scraperService()

    try:
        await browser.start()

        for i in range(attemps):
            logging.info(f"Ejecución {i+1}/{attemps}")
            await scraperService.process()

    except asyncio.CancelledError:
        logging.info("🛑 Cancelado por el usuario (Ctrl+C)")

    except Exception as e:
        logging.exception(f"🔴 Error durante la ejecución principal {e}")

    finally:
        try:
            if browser.isStarted:
                await browser.close()

            logging.info("🔌 Todos los recursos cerrados correctamente.")

        except Exception as e:
            logging.warning(f"🔴 Error al cerrar recursos: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.info("👋 Programa detenido por Ctrl+C")