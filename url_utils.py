
import re
from urllib.parse import urlsplit, urlunsplit


# URL normalization and validation
def normalize_url(url: str) -> str:
    """
    Normalize and validate a URL.

    - Removes surrounding whitespace.
    - Removes control characters.
    - Adds https:// if no scheme is provided.
    - Allows only HTTP and HTTPS.
    - Validates the hostname.
    """

    if not isinstance(url, str):
        raise ValueError("URL must be a string")

    # Remove control characters
    url = re.sub(r"[\x00-\x1f\x7f]", "", url).strip()

    if not url:
        raise ValueError("URL cannot be empty")

    # Add HTTPS when scheme is missing
    if "://" not in url:
        url = "https://" + url

    try:
        parsed = urlsplit(url)

        # Allow only HTTP and HTTPS
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Only HTTP and HTTPS URLs are allowed")

        # Hostname must exist
        if not parsed.hostname:
            raise ValueError("Invalid URL: hostname is missing")

        # Validate port if provided
        if parsed.port is not None:
            if not 1 <= parsed.port <= 65535:
                raise ValueError("Invalid port")

        # Reject whitespace in the hostname
        if any(char.isspace() for char in parsed.netloc):
            raise ValueError("Invalid URL hostname")

        return urlunsplit((
            parsed.scheme.lower(),
            parsed.netloc,
            parsed.path,
            parsed.query,
            parsed.fragment
        ))

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid URL") from exc
