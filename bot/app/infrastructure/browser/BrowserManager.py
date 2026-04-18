import shutil
import logging
import asyncio
import tempfile
from pathlib import Path

from pydoll.constants import Key
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.interactions.mouse import MouseTimingConfig

from app.domain.interfaces.IBrowserManager import IBrowserManager
from app.infrastructure.browser.FingerprintGenerator import FingerprintGenerator

class BrowserManager(IBrowserManager):
    def __init__(self, proxies: list, fingerprintGenerator: FingerprintGenerator, binaryLocation: str = None, remoteUrl: str = None, extraArgs: list = None):
        self.Key = Key
        self._tab = None
        self._proxyIndex = 0
        self._browser = None
        self._started = False
        self._repeatCount = 1
        self._profileDir = None
        self._proxies = proxies
        self._currentRepeat = 0
        self._currentProxy = None
        self._lock = asyncio.Lock()
        self.remote_url = remoteUrl
        self.extra_args = extraArgs or []
        self.binaryLocation = binaryLocation
        self._fingerprintGenerator = fingerprintGenerator

    @property
    def isStarted(self) -> bool:
        return self._started and self._browser is not None

    def _getNextProxy(self):
        proxy = self._proxies[self._proxyIndex]

        self._currentRepeat += 1
        if self._currentRepeat >= self._repeatCount:
            self._currentRepeat = 0
            self._proxyIndex = (self._proxyIndex + 1) % len(self._proxies)

        return proxy

    async def _applyFingerprint(self, fp: dict):
        # Navigator
        await self._tab.execute_script(f"""
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fp["platform"]}'
        }});

        Object.defineProperty(navigator, 'language', {{
            get: () => '{fp["language"]}'
        }});

        Object.defineProperty(navigator, 'languages', {{
            get: () => {fp["languages"]}
        }});

        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fp["hardwareConcurrency"]}
        }});

        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fp["deviceMemory"]}
        }});
        """)

        # WebGL
        await self._tab.execute_script(f"""
        const getParameter = WebGLRenderingContext.prototype.getParameter;

        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fp["webgl"]["vendor"]}';
            if (parameter === 37446) return '{fp["webgl"]["renderer"]}';
            return getParameter.call(this, parameter);
        }};
        """)

        # Timezone
        await self._tab.execute_script(f"""
        Intl.DateTimeFormat = class extends Intl.DateTimeFormat {{
            constructor(...args) {{
                super(...args);
                return new Proxy(this, {{
                    get(target, prop) {{
                        if (prop === 'resolvedOptions') {{
                            return () => ({{
                                timeZone: '{fp["timezone"]}'
                            }});
                        }}
                        return target[prop];
                    }}
                }});
            }}
        }};
        """)
    
    async def restart(self):
        logging.warning("♻️ Reiniciando navegador completo...")

        async with self._lock:
            if self._browser:
                try:
                    await asyncio.wait_for(
                        self._browser.__aexit__(None, None, None), timeout=10
                    )
                    logging.info("🔌 Navegador cerrado correctamente.")
                except asyncio.TimeoutError:
                    logging.warning("🟡 Timeout cerrando el navegador.")
                except Exception as e:
                    logging.warning(f"No se pudo cerrar el navegador: {e}")

                self._browser = None
                self._tab = None
                self._started = False

            if self._profileDir and self._profileDir.exists():
                try:
                    shutil.rmtree(self._profileDir, ignore_errors=True)
                    await asyncio.sleep(0.3)
                    logging.info("🧹 Perfil temporal eliminado.")
                except Exception as e:
                    logging.warning(f"No se pudo eliminar el perfil: {e}")

            self._profileDir = None

        try:
            await self.start()
        except Exception as e:
            logging.error(f"🔴 Falló reiniciar el navegador: {e}")
            async with self._lock:
                self._browser = None
                self._tab = None
                self._started = False
                self._profileDir = None
            raise

    async def start(self):
        fp = self._fingerprintGenerator.generate()
        
        async with self._lock:
            if self._started:
                logging.info("🟡 BrowserManager ya estaba iniciado.")
                return

            try:
                logging.info("🌐 Iniciando navegador...")

                proxy = self._getNextProxy()
                self._currentProxy = proxy

                # MODO REMOTO
                if self.remote_url:
                    logging.info(f"~ Conectando a navegador remoto: {self.remote_url}")
                    browser = await Chrome.connect(self.remote_url)
                    self._tab = browser
                    self._profileDir = None

                # MODO LOCAL
                else:
                    logging.info(f"~ Conectando a navegador local")
                    options = ChromiumOptions()

                    if self.binaryLocation:
                        options.binary_location = self.binaryLocation

                    ua = fp["userAgent"]
                    screen = fp["screen"]    
                    options.add_argument("--password-store=basic")

                    if proxy:
                        options.add_argument(f"--proxy-server={proxy}")

                    logging.info(f"🌐 Usando proxy: {proxy if proxy else 'LOCAL'}")

                    # Perfil SOLO en local
                    profileDir = Path(tempfile.mkdtemp(prefix="pydoll_"))
                    self._profileDir = profileDir
                    options.add_argument(f"--user-data-dir={profileDir}")

                    # Configurable
                    options.add_argument(f"--user-agent={ua}")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument(f"--window-size={screen['width']},{screen['height']}")

                    # Args externos
                    for arg in self.extra_args:
                        options.add_argument(arg)

                    browser = Chrome(options=options)
                    self._tab = await browser.start()
                    
                    # Aplicacion fingerPrint
                    await self._applyFingerprint(fp)

                # Mouse config
                self._tab.mouse.timing = MouseTimingConfig(
                    fitts_a=0.11,
                    fitts_b=0.22,
                    curvature_min=0.18,
                    curvature_max=0.42,
                    tremor_amplitude=1.6,
                    overshoot_probability=0.92,
                    min_duration=0.18,
                    max_duration=4.0,
                    frame_interval=0.014,
                )

                self._browser = browser
                self._started = True

                logging.info("🔵 BrowserManager iniciado exitosamente.")

            except Exception as e:
                logging.exception(f"🔴 Error iniciando navegador: {e}")

                if self._profileDir and self._profileDir.exists():
                    shutil.rmtree(self._profileDir, ignore_errors=True)

                if self._browser:
                    try:
                        await self._browser.__aexit__(None, None, None)
                    except Exception:
                        pass

                self._browser = None
                self._started = False
                raise

    async def getBrowser(self):
        if not self.isStarted or not self._tab:
            raise RuntimeError("BrowserManager no iniciado")
        return self._tab

    async def close(self):
        async with self._lock:
            if not self._browser:
                logging.info("🟡 Browser ya estaba cerrado.")
                return

            try:
                await self._browser.__aexit__(None, None, None)
                logging.info("🔌 Navegador cerrado correctamente.")
            except Exception as e:
                logging.exception(f"🔴 Error cerrando navegador: {e}")
                raise
            finally:
                self._browser = None
                self._started = False

                if self._profileDir and self._profileDir.exists():
                    try:
                        shutil.rmtree(self._profileDir, ignore_errors=True)
                        logging.info("🧹 Perfil eliminado.")
                    except Exception as e:
                        logging.warning(f"No se pudo eliminar perfil: {e}")

                self._profileDir = None