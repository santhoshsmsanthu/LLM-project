
import pytest

from url_utils import normalize_url


# Add a default HTTPS scheme
def test_add_https_to_domain():
    assert normalize_url("example.com") == "https://example.com"


# Reject unsupported FTP URLs
def test_reject_ftp_url():
    with pytest.raises(ValueError):
        normalize_url("ftp://x")


# Reject local file URLs
def test_reject_file_url():
    with pytest.raises(ValueError):
        normalize_url("file:///etc/passwd")


# Preserve valid HTTPS URLs
def test_preserve_https_url():
    assert normalize_url("https://example.com") == "https://example.com"


# Remove control characters from URLs
def test_remove_control_characters():
    assert normalize_url("example.com\n") == "https://example.com"


# Reject empty URL input
def test_reject_empty_url():
    with pytest.raises(ValueError):
        normalize_url("")
