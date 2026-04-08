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

class BrowserManager(IBrowserManager):
    def __init__(self):
        self._tab = None
        self._browser = None
        self._started = False
        self._profileDir = None
        self.Key = Key
        self._lock = asyncio.Lock()
        self._proxies = [
            # None,
            "http://154.53.34.203:8001",
            "http://154.53.34.203:8002",
        ]
        self._proxyIndex = 0
        self._currentProxy = None
        self._repeatCount = 3
        self._currentRepeat = 0

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
    
    async def restart(self):
        logging.warning("♻️ Reiniciando navegador completo...")

        # Cerrar navegador actual de manera segura
        async with self._lock:
            if self._browser:
                try:
                    await asyncio.wait_for(self._browser.__aexit__(None, None, None), timeout=10)
                    logging.info("🔌 Navegador cerrado correctamente.")
                except asyncio.TimeoutError:
                    logging.warning("⚠️ Timeout cerrando el navegador, forzando cleanup.")
                except Exception as e:
                    logging.warning(f"No se pudo cerrar el navegador: {e}")

                self._browser = None
                self._tab = None
                self._started = False

            # Eliminar perfil temporal
            if self._profileDir and self._profileDir.exists():
                try:
                    shutil.rmtree(self._profileDir, ignore_errors=True)
                    await asyncio.sleep(0.3)  # asegurar que el FS libere el handle
                    logging.info("🧹 Perfil temporal eliminado.")
                except Exception as e:
                    logging.warning(f"No se pudo eliminar el perfil temporal: {e}")

            self._profileDir = None

        # Iniciar nuevo navegador fuera del lock para evitar deadlocks
        try:
            await self.start()
        except Exception as e:
            logging.error(f"🔴 Falló reiniciar el navegador: {e}")
            # En caso crítico, aseguramos que no queden referencias colgando
            async with self._lock:
                self._browser = None
                self._tab = None
                self._started = False
                self._profileDir = None
            raise
        
    async def start(self):
        async with self._lock:
            if self._started:
                logging.info("🟡 BrowserManager ya estaba iniciado.")
                return

            try:
                ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"              
                profileDir = Path(tempfile.mkdtemp(prefix="pydoll_"))
                
                logging.info("🌐 Iniciando navegador Pydoll...")

                options = ChromiumOptions()
                # options.binary_location = "/usr/bin/chromium-browser"
                options.binary_location = "/usr/bin/microsoft-edge"
                
                # PROXY
                proxy = self._getNextProxy()
                self._currentProxy = proxy
                options.add_argument("--password-store=basic")

                logging.info(f"🌐 Usando proxy: {proxy if proxy else 'LOCAL'}")
                
                # PROXY
                if proxy:
                    options.add_argument(f"--proxy-server={proxy}")

                # PERFIL TEMPORAL
                options.add_argument(f"--user-data-dir={profileDir}")

                # USER AGENT ALEATORIO
                options.add_argument(f"--user-agent={ua}")

                # ANTI-DETECCIÓN
                options.add_argument("--disable-blink-features=AutomationControlled")

                # TAMAÑO DE VENTANA
                options.add_argument("--window-size=1920,1080")

                # WSL / Docker estabilidad
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")

                # IDIOMA
                options.add_argument("--lang=es-CO")
                
                browser = Chrome(options = options)

                # levantar Chrome
                self._tab = await browser.start()
                
                await self._tab.execute_script(
                    """
                        Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
                        Object.defineProperty(navigator,'platform',{get:()=>'Win32'});
                        Object.defineProperty(navigator,'vendor',{get:()=>'Google Inc.'});
                        window.chrome = {runtime:{}};
                    """
                )
                self._profileDir = profileDir
                
                queryUrl ="https://procesojudicial.ramajudicial.gov.co/Justicia21/Administracion/Ciudadanos/frmConsulta"
                await self._tab.go_to(queryUrl)

                
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
                
                # SOLO asignar si todo salió bien
                self._browser = browser
                self._started = True

                logging.info("🔵 BrowserManager iniciado exitosamente.")

            except Exception as e:
                logging.exception(f"🔴 Error crítico iniciando el navegador: {e}")
                
                if profileDir and profileDir.exists():
                    shutil.rmtree(profileDir, ignore_errors=True)

                # Cleanup defensivo si algo falló a mitad
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
            raise RuntimeError("BrowserManager no iniciado o tab no disponible")
        try:
            return self._tab
        except Exception as e:
            logging.error(f"🔴 Error creando nueva tab: {e}")
            raise

    async def close(self):
        async with self._lock:
            if not self._browser:
                logging.info("🟡 Browser ya estaba cerrado.")
                return

            try:
                await self._browser.__aexit__(None, None, None)
                logging.info("🔌 Navegador cerrado correctamente.")

            except Exception as e:
                logging.exception(f"🔴 Error cerrando el navegador: {e}")
                raise
            
            finally:
                self._browser = None
                self._started = False
                
                if self._profileDir and self._profileDir.exists():
                    try:
                        shutil.rmtree(self._profileDir, ignore_errors=True)
                        logging.info("🧹 Perfil temporal eliminado.")
                    except Exception as e:
                        logging.warning(f"No se pudo eliminar el perfil temporal: {e}")

                self._profileDir = None
