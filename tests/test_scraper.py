
from unittest.mock import patch, Mock

import pytest

from page_scraper import scrape_website
from scraper_exceptions import (
    BlockedError,
    EmptyContentError,
    InvalidURLError,
    ScraperError,
)


# Successful scraping and metadata extraction
def test_normal_homepage_returns_text_and_metadata():

    fake_html = """
    <html>
        <head>
            <title>ABC Technologies</title>
            <meta name="description"
                  content="Software development company">
        </head>

        <body>
            <nav>Home About Contact</nav>

            <h1>ABC Technologies</h1>

            <p>
                We provide software development services.
            </p>

            <h2>Our Services</h2>

            <script>
                console.log("Remove this");
            </script>

            <footer>Copyright 2026</footer>
        </body>
    </html>
    """

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = fake_html

    with patch(
        "page_scraper.requests.get",
        return_value=mock_response
    ) as mock_get:

        text, metadata = scrape_website("example.com")

    # Verify extracted text
    assert "ABC Technologies" in text
    assert "software development services" in text

    # Verify unwanted content is removed
    assert "console.log" not in text
    assert "Copyright 2026" not in text

    # Verify metadata
    assert metadata["title"] == "ABC Technologies"
    assert metadata["description"] == "Software development company"
    assert "Our Services" in metadata["headings"]
    assert metadata["status_code"] == 200

    # Verify the mocked HTTP request
    mock_get.assert_called_once()


# Blocked website detection
def test_access_denied_raises_blocked_error():

    fake_html = """
    <html>
        <body>
            <h1>403 Access Denied</h1>
            <p>Your request has been blocked.</p>
        </body>
    </html>
    """

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = fake_html

    with patch(
        "page_scraper.requests.get",
        return_value=mock_response
    ):

        with pytest.raises(BlockedError):
            scrape_website("example.com")


# Empty readable-content detection
def test_empty_page_raises_empty_content_error():

    fake_html = """
    <html>
        <head>
            <title></title>
        </head>

        <body>
            <script>
                console.log("Nothing useful");
            </script>

            <style>
                body { color: red; }
            </style>
        </body>
    </html>
    """

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = fake_html

    with patch(
        "page_scraper.requests.get",
        return_value=mock_response
    ):

        with pytest.raises(EmptyContentError):
            scrape_website("example.com")


# Invalid URL exception typing
def test_invalid_url_raises_typed_scraper_error():

    with pytest.raises(InvalidURLError):
        scrape_website("ftp://example.com")


# Per-merchant failure result handling
def test_scraper_failures_are_safe_to_handle_per_merchant():

    with pytest.raises(ScraperError) as error:
        scrape_website("not a valid url")

    failed_merchant = {
        "status": "failed",
        "error": str(error.value),
    }

    assert failed_merchant["status"] == "failed"
    assert failed_merchant["error"]
