
# Scraper failure exception hierarchy
class ScraperError(Exception):
    """Base exception for website scraping errors."""


class InvalidURLError(ScraperError):
    """Raised when a website URL is invalid or unsupported."""


class BlockedError(ScraperError):
    """Raised when a website blocks the scraper."""


class EmptyContentError(ScraperError):
    """Raised when a website has no useful readable content."""


class ScraperRequestError(ScraperError):
    """Raised when the HTTP request fails."""


class ScraperHTTPError(ScraperError):
    """Raised when the website returns an HTTP error."""
