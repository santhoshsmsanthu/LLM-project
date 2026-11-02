
import pytest

from llm_vertex import parse_llm_json, LLMError


def test_valid_json():

    raw = '{"mcc_code": "7372", "risk": "Low"}'

    result = parse_llm_json(raw)

    assert result["mcc_code"] == "7372"
    assert result["risk"] == "Low"


def test_fenced_json():

    raw = """
    ```json
    {
        "mcc_code": "7372",
        "risk": "Low"
    }
    ```
    """

    result = parse_llm_json(raw)

    assert result["mcc_code"] == "7372"
    assert result["risk"] == "Low"


def test_nested_case_insensitive_json():

    raw = """
    {
        "MCC": {
            "MCC_Code": "7372"
        }
    }
    """

    result = parse_llm_json(raw)

    assert result["mcc"]["mcc_code"] == "7372"


def test_malformed_json():

    raw = """
    {
        "mcc_code": "7372",
        "risk": "Low"
    """

    with pytest.raises(LLMError):
        parse_llm_json(raw)


def test_empty_response():

    with pytest.raises(LLMError):
        parse_llm_json("")


def test_json_with_extra_text():

    raw = """
    Here is the classification result:

    {
        "MCC_Code": "7372",
        "Risk": "Low"
    }
    """

    result = parse_llm_json(raw)

    assert result["mcc_code"] == "7372"
    assert result["risk"] == "Low"
