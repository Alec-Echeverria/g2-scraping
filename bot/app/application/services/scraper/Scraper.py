import logging
import asyncio
from pathlib import Path
from datetime import datetime

from typing import List, Dict, Any

from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IBrowserManager import IBrowserManager

from app.domain.exceptions.ScraperException import (
    ScraperException,
    BlockException,
    DOMException,
    TimeoutException,
    NetworkException,
    ProxyException
)


class Scraper(IScraper):
    def __init__(self, url: str, browserManager: IBrowserManager, retries: int, pages: int):
        self.url = url
        self.pages = pages
        self.retries = retries
        self.browserManager = browserManager

    async def _captureError(self, tab, folderName: Path, page: int, error: Exception, step: str):
        try:
            if not tab:
                return

            errorCode = getattr(error, "code", "UNKNOWN")

            dirPath: Path = folderName / "errors" / f"page_{page}"
            dirPath.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            filePath = dirPath / f"{step}_{errorCode}_{timestamp}.png"

            await tab.take_screenshot(path=str(filePath))

            logging.warning(f"Screenshot saved: {filePath}")

        except Exception as e:
            logging.warning(f"No se pudo guardar screenshot: {e}")


    async def _retry(self, fn, *args, **kwargs):
        lastException = None

        for attempt in range(1, self.retries + 1):
            try:
                return await fn(*args, **kwargs)

            except ScraperException as e:
                lastException = e

                logging.warning(f"🟡 Attempt {attempt} failed [{e.code}]: {e}")

                if isinstance(e, BlockException):
                    logging.warning("🚨 BLOQUEO detectado (captcha / IP ban)")

                elif isinstance(e, TimeoutException):
                    logging.warning("⏱ Timeout detectado")

                elif isinstance(e, DOMException):
                    logging.warning("🧩 DOM cambió")

                elif isinstance(e, ProxyException):
                    logging.warning("🌐 Proxy error")

                elif isinstance(e, NetworkException):
                    logging.warning("📡 Network issue")

                await self.browserManager.restart()
                await asyncio.sleep(3)

            except Exception as e:
                lastException = NetworkException(
                    str(e),
                    code="UNKNOWN",
                    context={"raw": str(e)}
                )

                logging.warning(f"🟡 Unknown error: {e}")

                await self.browserManager.restart()
                await asyncio.sleep(3)

        logging.error("🔴 All retries failed")
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
            raise TimeoutException(
                "No se pudo obtener totalPages",
                code="TIMEOUT",
                context={"error": str(e)}
            )

    async def _extractAll(self, tab, page: int, folderName: Path) -> List[Dict[str, Any]]:
        results = []

        try:
            container = await tab.find(id="product-cards", timeout=10)

            cards = await container.find(
                xpath='.//div[@data-ordered-events-item="products"]',
                find_all=True,
            )

            logging.info(f"Productos encontrados {len(cards)}")

            for i, card in enumerate(cards):

                try:
                    cards = await container.find(
                        xpath='.//div[@data-ordered-events-item="products"]',
                        find_all=True
                    )

                    if i >= len(cards):
                        continue

                    card = cards[i]

                    titleEl = await card.find(class_name="product-card__product-name-text")
                    title = (await titleEl.text).strip()

                    vendorEl = await card.find(
                        tag_name="a",
                        class_name="a--sm",
                        raise_exc=False
                    )
                    vendor = (await vendorEl.text).strip() if vendorEl else None

                    rating = None
                    ratingEl = await card.find(
                        xpath='.//span[contains(@class,"fw-semibold")]',
                        raise_exc=False
                    )

                    if ratingEl:
                        text = (await ratingEl.text).strip()
                        if text.replace('.', '', 1).isdigit():
                            rating = text

                    descEl = await card.find(
                        class_name="product-listing__paragraph",
                        raise_exc=False
                    )
                    description = (await descEl.text).strip() if descEl else None

                    results.append({
                        "title": title,
                        "vendor": vendor,
                        "rating": rating,
                        "description": description,
                        "page": page,
                        "index": i
                    })

                except Exception as e:
                    await self._captureError(tab, folderName, page, e, f"card_{i}")

                    raise DOMException(
                        f"Error extrayendo card page={page} index={i}",
                        code="DOM_ERROR",
                        context={
                            "page": page,
                            "index": i,
                            "title": title,
                            "error": str(e)
                        }
                    )

        except Exception as e:
            await self._captureError(tab, folderName, page, e, "extract_all")

            raise DOMException(
                f"Error en extracción página {page}",
                code="DOM_ERROR",
                context={"page": page, "error": str(e)}
            )

        return results

    async def _loadPage(self, url):
        tab = await self.browserManager.getBrowser()

        await tab.go_to(url)
        await tab.find(id="product-cards", timeout=10)

        container = await tab.find(id="product-cards", timeout=5)
        cards = await container.find(
            xpath='.//div[@data-ordered-events-item="products"]',
            find_all=True,
        )

        if not cards:
            raise BlockException(
                "No products detected (possible block/captcha)",
                code="BLOCKED",
                context={"url": url}
            )

        return tab

    async def _processPage(self, url, page, folderName: Path):
        tab = await self._retry(self._loadPage, url)
        return await self._extractAll(tab, page, folderName)

    async def scraping(self, folderName: Path) -> List[Dict[str, Any]]:
        try:
            allResults: List[Dict[str, Any]] = []

            tab = await self._retry(self._loadPage, self.url)

            await asyncio.sleep(5)

            totalPages = await self._getTotalPages(tab)

            if self.pages > totalPages:
                raise ValueError(
                    f"pages ({self.pages}) > totalPages ({totalPages})"
                )

            logging.info(f"Total páginas detectadas: {totalPages}")

            for page in range(1, min(self.pages, totalPages) + 1):
                url = f"{self.url}?page={page}"
                logging.info(f"Página: {page}")

                try:
                    results = await self._processPage(url, page, folderName)
                    allResults.extend(results)
                    await asyncio.sleep(2)

                except ScraperException as e:
                    logging.error(f"🔴 Scraper error page {page} [{e.code}]: {e}")

                except Exception as e:
                    logging.error(f"🔴 Unexpected error page {page}: {e}")

            return allResults

        except ScraperException as e:
            logging.error(f"🔴 Scraper fatal error [{e.code}]: {e}")
            raise

        except Exception as e:
            logging.exception(f"🔴 Global error: {e}")
            raise