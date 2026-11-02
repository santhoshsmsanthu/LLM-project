
import json
import logging
import re
import time

from google import genai
from google.genai import types

from settings import settings


logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when Gemini integration fails."""


def normalize_keys(data):
    """
    Recursively convert dictionary keys to lowercase.
    """

    if isinstance(data, dict):
        return {
            str(key).lower(): normalize_keys(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [normalize_keys(item) for item in data]

    return data


def parse_llm_json(raw: str) -> dict:
    """
    Convert Gemini response text into a Python dictionary.

    Supports:
    - Normal JSON
    - Markdown fenced JSON
    - Nested JSON
    - Case-insensitive dictionary keys
    """

    if not isinstance(raw, str) or not raw.strip():
        raise LLMError("Gemini returned an empty response")

    # Remove Markdown code fences
    cleaned = raw.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError:
        # Handle additional text surrounding a JSON object
        try:
            start = cleaned.index("{")
            result, _ = json.JSONDecoder().raw_decode(cleaned[start:])

        except (ValueError, json.JSONDecodeError) as exc:
            raise LLMError(
                "Gemini returned malformed JSON"
            ) from exc

    if not isinstance(result, dict):
        raise LLMError("Expected a JSON object from Gemini")

    return normalize_keys(result)


def call_gemini(prompt: str) -> dict:
    """
    Send a prompt to Gemini through Vertex AI.

    Retries up to four times with exponential backoff.
    """

    if not prompt or not prompt.strip():
        raise LLMError("Prompt cannot be empty")

    if not settings.GOOGLE_CLOUD_PROJECT:
        raise LLMError("GOOGLE_CLOUD_PROJECT is not configured")

    if not settings.VERTEX_MODEL:
        raise LLMError("VERTEX_MODEL is not configured")

    client = None

    try:
        # Initialize Google Gen AI SDK for Vertex AI
        client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
            http_options=types.HttpOptions(
                api_version="v1",
                timeout=30_000
            )
        )

        for attempt in range(4):

            try:
                logger.info(
                    "Sending Gemini request. Attempt %s/4",
                    attempt + 1
                )

                response = client.models.generate_content(
                    model=settings.VERTEX_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

                if not response.text:
                    raise LLMError(
                        "Gemini returned an empty response"
                    )

                result = parse_llm_json(response.text)

                logger.info("Gemini response received successfully")

                return result

            except Exception as exc:

                logger.warning(
                    "Gemini request failed on attempt %s: %s",
                    attempt + 1,
                    exc
                )

                if attempt == 3:
                    break

                delay = 2 ** attempt

                logger.info(
                    "Retrying Gemini request in %s seconds",
                    delay
                )

                time.sleep(delay)

        raise LLMError(
            "Gemini failed after 4 attempts"
        )

    except LLMError:
        raise

    except Exception as exc:
        raise LLMError(
            f"Gemini initialization failed: {exc}"
        ) from exc

    finally:
        if client is not None:
            client.close()
