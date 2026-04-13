import logging
import asyncio
from typing import List, Dict, Any

from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IBrowserManager import IBrowserManager

class Scraper(IScraper):
    def __init__(self, url: str, browserManager: IBrowserManager):
        self.url = url
        self.browserManager = browserManager
        self.retries = 2
    
    async def _retry(self, fn, *args, **kwargs):
        lastException = None

        for attempt in range(1, self.retries + 1):
            try:
                return await fn(*args, **kwargs)

            except Exception as e:
                lastException = e
                logging.warning(f"🟡 Intento {attempt} falló: {e}")

                await self.browserManager.restart()
                await asyncio.sleep(3)

        logging.error("🔴 Todos los reintentos fallaron")
        raise lastException

    async def _getTotalPages(self, tab) -> int:
        try:
            res = await tab.execute_script("""
                const links = document.querySelectorAll('.pagination a');

                const nums = Array.from(links)
                    .map(a => parseInt(a.textContent.trim()))
                    .filter(n => !isNaN(n));

                return nums.length ? Math.max(...nums) : 1;
            """)

            return res["result"]["result"]["value"]

        except Exception as e:
            logging.warning(f"🟡 No se pudo obtener totalPages: {e}")
            return 1

    async def _extractAll(self, tab, page: int) -> List[Dict[str, Any]]:
        results = []

        try:
            container = await tab.find(id="product-cards", timeout=10)

            cards = await container.find(
                xpath='.//div[@data-ordered-events-item="products"]',
                find_all=True,
            )

            logging.info(f"Productos encontrados {len(cards)}")

            for i, card in enumerate(cards):
                title = "UNKNOWN"

                try:
                    # Evitar Stale
                    cards = await container.find(
                        xpath='.//div[@data-ordered-events-item="products"]',
                        find_all=True
                    )

                    # Protección por si cambió el DOM
                    if i >= len(cards):
                        continue

                    card = cards[i]
                    
                    titleEl = await card.find(
                        class_name="product-card__product-name-text"
                    )
                    title = (await titleEl.text).strip()

                    vendorEl = await card.find(
                        tag_name="a",
                        class_name="a--sm",
                        raise_exc=False
                    )
                    vendor = (await vendorEl.text).strip() if vendorEl else None
                    
                    # Rating
                    rating = None
                    ratingEl = await card.find(
                        xpath='.//span[contains(@class,"fw-semibold")]',
                        raise_exc=False
                    )

                    if ratingEl:
                        text = (await ratingEl.text).strip()

                        # solo aceptar números tipo 4 o 4.5
                        if text.replace('.', '', 1).isdigit():
                            rating = text

                    # DESCRIPTION
                    descEl = await card.find(
                        class_name="product-listing__paragraph",
                        raise_exc=False
                    )
                    description = (await descEl.text).strip() if descEl else None

                    data = {
                        "title": title,
                        "vendor": vendor,
                        "rating": rating,
                        "description": description,
                        "page": page,
                        "index": i
                    }

                    results.append(data)

                except Exception as e:
                    logging.error(f"🟡 Error en card [page={page} index={i} title={title}] → {e}")
                    continue

        except Exception as e:
            logging.error(f"🔴 Error en extracción página {page}: {e}")

        return results
    
    async def _loadPage(self, url):
        tab = await self.browserManager.getBrowser()

        await tab.go_to(url)
        await tab.find(id="product-cards", timeout=10)

        # Detectar bloqueo
        container = await tab.find(id="product-cards", timeout=5)
        cards = await container.find(
            xpath='.//div[@data-ordered-events-item="products"]',
            find_all=True,
        )

        if not cards:
            raise Exception("Posible bloqueo: sin productos")

        return tab

    async def _processPage(self, url, page):
        tab = await self._retry(self._loadPage, url)
        return await self._extractAll(tab, page)

    # Scraping 
    async def scraping(self) -> List[Dict[str, Any]]:
        try:
            allResults: List[Dict[str, Any]] = []

            # Primera carga
            tab = await self._retry(self._loadPage, self.url)

            await asyncio.sleep(5)

            totalPages = await self._getTotalPages(tab)
            logging.info(f"Total páginas detectadas: {totalPages}")

            # Loop de páginas
            for page in range(1, totalPages + 1):
                url = f"{self.url}?page={page}"
                logging.info(f"Página: {page}")

                try:
                    results = await self._processPage(url, page)

                    allResults.extend(results)

                    await asyncio.sleep(2)

                except Exception as e:
                    logging.error(f"🔴 Página {page} falló completamente: {e}")

            return allResults

        except Exception as e:
            logging.exception(f"🔴 Error global en scraping: {e}")
            await self.browserManager.restart()
            return []
    