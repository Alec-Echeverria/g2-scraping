class ScraperException(Exception):
    def __init__(self, message: str, code: str = "SCRAPER_ERROR", context: dict = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

class DOMException(ScraperException):
    pass

class ProxyException(ScraperException):
    pass

class NetworkException(ScraperException):
    pass

class TimeoutException(ScraperException):
    pass

class BlockException(ScraperException):
    pass
