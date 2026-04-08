import time
import random
from typing import Any

class FingerprintGenerator:
    _OS_PROFILES: list[dict[str, Any]] = [
        {
            "platform": "Win32",
            "userAgents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            ],
            "webglRenderers": [
                "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (Intel, Intel(R) HD Graphics 520 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0)",
            ],
            "concurrencyLevels": [4, 6, 8, 12, 16],
            "memoryLevels": [4, 8, 16, 32],
            "maxTouchPoints": [0, 2, 10],
        },
    ]

    _COLOMBIA_REGION: dict[str, Any] = {
        "timezone": "America/Bogota",
        "timezoneOffset": 300,
        "languages": ["es-CO", "es", "en-US"],
        "language": "es-CO",
        "connection": {"effectiveType": "4g", "rtt": 50, "downlink": 10, "saveData": False},
    }

    _RESOLUTIONS: list[dict[str, Any]] = [
        {"width": 1920, "height": 1080, "pixelRatio": 1, "colorDepth": 24, "pixelDepth": 24, "taskbarHeight": 40},
        {"width": 1366, "height": 768, "pixelRatio": 1, "colorDepth": 24, "pixelDepth": 24, "taskbarHeight": 40},
        {"width": 1536, "height": 864, "pixelRatio": 1.25, "colorDepth": 24, "pixelDepth": 24, "taskbarHeight": 48},
        {"width": 1440, "height": 900, "pixelRatio": 1, "colorDepth": 24, "pixelDepth": 24, "taskbarHeight": 40},
    ]

    def __init__(self, seed: str):
        self.seed = seed
        self._rng = random.Random(int(hash(seed)) % (2 ** 31))

    def _pick_webgl_vendor(self, renderer: str) -> str:
        if "NVIDIA" in renderer or "GeForce" in renderer:
            return "Google Inc. (NVIDIA)"
        if "AMD" in renderer or "Radeon" in renderer:
            return "Google Inc. (AMD)"
        return "Google Inc. (Intel)"

    def _extract_app_version(self, user_agent: str) -> str:
        try:
            start = user_agent.index("(")
            end = user_agent.index(")", start)
            return user_agent[start + 1: end]
        except ValueError:
            return ""

    def _choice(self, items):
        return self._rng.choice(items)

    def _randint(self, a, b):
        return self._rng.randint(a, b)

    def _random(self):
        return self._rng.random()

    def generate(self) -> dict[str, Any]:
        os_profile = self._choice(self._OS_PROFILES)
        user_agent = self._choice(os_profile["userAgents"])
        renderer = self._choice(os_profile["webglRenderers"])
        resolution = self._choice(self._RESOLUTIONS)
        region = self._COLOMBIA_REGION

        avail_height = (
            resolution["height"]
            - resolution["taskbarHeight"]
            - self._randint(0, 20)
        )

        return {
            "id": f"fp_{self.seed}_{int(time.time() * 1000)}_{self._randint(1000, 9999)}",
            "platform": os_profile["platform"],
            "userAgent": user_agent,
            "appVersion": self._extract_app_version(user_agent),
            "appCodeName": "Mozilla",
            "appName": "Netscape",
            "appVendor": "Google Inc.",
            "vendorSub": "",
            "product": "Gecko",
            "productSub": "20030107",
            "hardwareConcurrency": self._choice(os_profile["concurrencyLevels"]),
            "deviceMemory": self._choice(os_profile["memoryLevels"]),
            "maxTouchPoints": self._choice(os_profile["maxTouchPoints"]),
            "screen": {
                "width": resolution["width"],
                "height": resolution["height"],
                "availWidth": resolution["width"] - self._randint(0, 10),
                "availHeight": avail_height,
                "availLeft": self._randint(0, 10),
                "availTop": self._randint(0, 10),
                "colorDepth": resolution["colorDepth"],
                "pixelDepth": resolution["pixelDepth"],
                "pixelRatio": resolution["pixelRatio"],
            },
            "timezone": region["timezone"],
            "timezoneOffset": region["timezoneOffset"],
            "languages": list(region["languages"]),
            "language": region["language"],
            "webgl": {
                "vendor": self._pick_webgl_vendor(renderer),
                "renderer": renderer,
                "version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                "shadingLanguageVersion": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
            },
            "cookieEnabled": True,
            "doNotTrack": "1" if self._random() > 0.8 else None,
            "webdriver": False,
            "pdfViewerEnabled": True,
            "connection": dict(region["connection"]),
        }
