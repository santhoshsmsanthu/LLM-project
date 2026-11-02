
import logging
from typing import Any

from url_utils import normalize_url
from page_scraper import scrape_website
from client_registry import get_client_config
from prompt_template import build_mcc_prompt
from llm_vertex import call_gemini

logger = logging.getLogger(__name__)


class MccClassificationError(Exception):
    """Custom exception for MCC classification failures."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def _get_predicted_mcc(llm_out: dict) -> str:
    """Extract the predicted MCC from the Gemini response."""

    possible_keys = [
        "predicted_mcc",
        "mcc",
        "mcc_code",
        "predicted_mcc_code",
    ]

    for key in possible_keys:
        value = llm_out.get(key)
        if value is not None:
            return str(value).strip()

    raise MccClassificationError(
        "Gemini response does not contain a predicted MCC",
        status_code=502,
    )


def _get_risk(predicted_mcc: str, risk_map: dict) -> Any:
    """Find the risk configuration for the predicted MCC."""

    return risk_map.get(predicted_mcc, "Unknown")


def classify(
    url: str,
    mcc: str,
    scraped_content: str,
    client: str,
    meta: dict | None = None,
) -> dict:
    """
    Classify a website and compare its predicted MCC
    with the claimed MCC.

    Args:
        url: Website URL.
        mcc: Claimed MCC code.
        scraped_content: Previously scraped website content.
        client: Client configuration name.
        meta: Optional website metadata.

    Returns:
        Dictionary containing MCC response, prediction and URL.
    """

    try:
        # 1. Normalize URL
        url = normalize_url(url)

        if not url:
            raise MccClassificationError(
                "Invalid website URL",
                status_code=400,
            )

        # 2. Use existing content or scrape the website
        meta = meta or {}

        if not scraped_content or len(scraped_content.strip()) < 200:
            logger.info("Scraping website: %s", url)

            scraped_content, scraped_meta = scrape_website(url)

            if scraped_meta:
                meta.update(scraped_meta)

        text = scraped_content or ""

        if not text.strip():
            raise MccClassificationError(
                "Unable to retrieve website content",
                status_code=502,
            )

        # 3. Load client MCC and risk configurations
        mcc_map, risk_map = get_client_config(client)

        if not isinstance(mcc_map, dict):
            raise MccClassificationError(
                "Invalid MCC configuration",
                status_code=500,
            )

        if not isinstance(risk_map, dict):
            raise MccClassificationError(
                "Invalid risk configuration",
                status_code=500,
            )

        # 4. Build Gemini prompt
        classification_rules = [
            f"{code}: {configuration}"
            for code, configuration in mcc_map.items()
        ]
        prompt = build_mcc_prompt(url, text, classification_rules)

        # 5. Get Gemini prediction
        llm_out = call_gemini(prompt)

        if not isinstance(llm_out, dict):
            raise MccClassificationError(
                "Invalid Gemini response",
                status_code=502,
            )

        predicted_mcc = _get_predicted_mcc(llm_out)

        # 6. Compare claimed and predicted MCC
        claimed_mcc = str(mcc).strip()

        mcc_match = claimed_mcc == predicted_mcc

        first_digit_diff = (
            claimed_mcc[0] != predicted_mcc[0]
            if claimed_mcc and predicted_mcc
            else False
        )

        # 7. Determine risk and out-of-scope status
        out_of_scope = predicted_mcc not in mcc_map

        risk = _get_risk(predicted_mcc, risk_map)

        # 8. Build final response
        return {
            "mcc_response": {
                "claimed_mcc": claimed_mcc,
                "predicted_mcc": predicted_mcc,
                "mcc_match": mcc_match,
                "first_digit_diff": first_digit_diff,
                "risk": risk,
                "out_of_scope": out_of_scope,
            },
            "mcc_prediction": llm_out,
            "url": url,
        }

    except MccClassificationError:
        raise

    except Exception as exc:
        logger.exception("MCC classification failed")

        raise MccClassificationError(
            f"MCC classification failed: {str(exc)}",
            status_code=500,
        ) from exc
