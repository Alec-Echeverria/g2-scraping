import time
import random
from typing import Any

class FingerprintGenerator:
    def __init__(self, seed: str, config: dict, regionCode: str = ..., osType: str = ...  ):
        self.seed = seed
        self.osType = osType
        self._rng = random.Random(int(hash(seed)) % (2 ** 31))
        self._OS_PROFILES = config["os_profiles"]
        self._RESOLUTIONS = config["resolutions"]
        self._REGION = config["regions"][regionCode]
          
    def _pick_webglVendor(self, renderer: str) -> str:
        if "NVIDIA" in renderer:
            return "Google Inc. (NVIDIA)"
        if "AMD" in renderer:
            return "Google Inc. (AMD)"
        return "Google Inc. (Intel)"

    def _extractAppVersion(self, user_agent: str) -> str:
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
        os_profiles = [
            p for p in self._OS_PROFILES
            if p["platform"] == self.osType
        ]

        if not os_profiles:
            raise ValueError(f"OS '{self.osType}' no existe en config")

        os_profile = self._choice(os_profiles)

        user_agent = self._choice(os_profile["userAgents"])
        renderer = self._choice(os_profile["webglRenderers"])
        resolution = self._choice(self._RESOLUTIONS)
        region = self._REGION

        avail_height = (
            resolution["height"]
            - resolution["taskbarHeight"]
            - self._randint(0, 20)
        )

        return {
            "id": f"fp_{self.seed}_{int(time.time() * 1000)}_{self._randint(1000, 9999)}",
            "platform": os_profile["platform"],
            "userAgent": user_agent,
            "appVersion": self._extractAppVersion(user_agent),
            "hardwareConcurrency": self._choice(os_profile["concurrencyLevels"]),
            "deviceMemory": self._choice(os_profile["memoryLevels"]),
            "maxTouchPoints": self._choice(os_profile["maxTouchPoints"]),
            "screen": {
                "width": resolution["width"],
                "height": resolution["height"],
                "availWidth": resolution["width"] - self._randint(0, 10),
                "availHeight": avail_height,
                "colorDepth": resolution["colorDepth"],
                "pixelDepth": resolution["pixelDepth"],
                "pixelRatio": resolution["pixelRatio"],
            },
            "timezone": region["timezone"],
            "timezoneOffset": region["timezoneOffset"],
            "languages": list(region["languages"]),
            "language": region["language"],
            "webgl": {
                "vendor": self._pick_webglVendor(renderer),
                "renderer": renderer,
            },
            "connection": dict(region["connection"]),
        }
    