
import logging
import re

import requests
from bs4 import BeautifulSoup, FeatureNotFound
from bs4.builder import ParserRejectedMarkup

from url_utils import normalize_url
from scraper_exceptions import (
    BlockedError,
    EmptyContentError,
    InvalidURLError,
    ScraperHTTPError,
    ScraperRequestError,
)


logger = logging.getLogger(__name__)


# Website download, validation, and readable-text extraction
def scrape_website(url: str) -> tuple[str, dict]:
    """
    Download a website and extract clean readable text.

    Returns:
        tuple[str, dict]: Extracted text and page metadata.

    Raises:
        BlockedError: Website blocks the request.
        EmptyContentError: No useful readable content.
        ScraperHTTPError: HTTP error response.
        ScraperRequestError: Network or request failure.
    """

    # 1. Normalize and validate URL
    try:
        normalized_url = normalize_url(url)
    except ValueError as exc:
        raise InvalidURLError(f"Invalid website URL: {exc}") from exc

    # 2. Configure request headers
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        # 3. Fetch website HTML
        response = requests.get(
            normalized_url,
            headers=headers,
            timeout=15,
        )

    except requests.RequestException as exc:
        logger.warning("Website request failed: %s", normalized_url)
        raise ScraperRequestError(
            f"Could not fetch website: {exc}"
        ) from exc

    # 4. Check HTTP status
    if response.status_code in (401, 403, 429):
        raise BlockedError(
            f"Website blocked the request. Status: {response.status_code}"
        )

    if response.status_code >= 400:
        raise ScraperHTTPError(
            f"Website returned HTTP {response.status_code}"
        )

    # 5. Parse HTML
    try:
        soup = BeautifulSoup(response.text, "lxml")
    except (FeatureNotFound, ParserRejectedMarkup) as exc:
        raise ScraperRequestError(
            "Could not parse website HTML"
        ) from exc

    # 6. Detect access denied and CAPTCHA pages
    page_text = soup.get_text(" ", strip=True)
    detection_text = page_text.lower()

    blocked_phrases = [
        "access denied",
        "403 forbidden",
        "request blocked",
        "captcha",
        "verify you are human",
        "unusual traffic",
    ]

    if any(phrase in detection_text for phrase in blocked_phrases):
        raise BlockedError(
            "Website returned an access denied or CAPTCHA page"
        )

    # 7. Extract page title
    title = ""

    if soup.title:
        title = soup.title.get_text(strip=True)

    # 8. Extract meta description
    description = ""

    meta_description = soup.find(
        "meta",
        attrs={"name": re.compile(r"^description$", re.I)}
    )

    if meta_description:
        description = meta_description.get("content", "").strip()

    # 9. Extract headings before removing unwanted elements
    headings = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        )
    ]

    # 10. Remove unnecessary HTML elements
    unwanted_tags = [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "noscript",
        "iframe",
        "svg",
    ]

    for tag in soup.find_all(unwanted_tags):
        tag.decompose()

    # 11. Extract readable text
    clean_text = soup.get_text(
        separator=" ",
        strip=True
    )

    # Normalize multiple spaces and newlines
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # 12. Detect empty content
    if not clean_text:
        raise EmptyContentError(
            "Website contains no readable text"
        )

    # 13. Prepare metadata
    metadata = {
        "url": normalized_url,
        "title": title,
        "description": description,
        "headings": headings,
        "status_code": response.status_code,
    }

    logger.info(
        "Successfully scraped website: %s",
        normalized_url
    )

    # 14. Return text and metadata
    return clean_text, metadata
