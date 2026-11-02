from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)

REQUEST = {
    "url": "https://example.com",
    "mcc": "5732",
    "scraped_content": (
        "ABC Technologies provides computer software and IT services to "
        "business customers. The company develops software solutions and "
        "offers technology consulting services to organizations worldwide. "
        "Its products include enterprise applications, cloud integrations, "
        "technical support, and consulting for businesses in multiple "
        "industries."
    ),
    "client": "default",
    "meta": {},
}

GEMINI_RESPONSE = {
    "predicted_mcc": "5732",
    "confidence": 0.96,
    "reason": "The company provides software services.",
}


@patch("mcc_classifier.scrape_website")
@patch("mcc_classifier.call_gemini", return_value=GEMINI_RESPONSE)
def test_new_classification_endpoint(mock_gemini, mock_scrape):
    response = client.post("/api/mcc/classify", json=REQUEST)

    assert response.status_code == 200
    assert response.json() == {
        "mcc_response": {
            "claimed_mcc": "5732",
            "predicted_mcc": "5732",
            "mcc_match": True,
            "first_digit_diff": False,
            "risk": "Unknown",
            "out_of_scope": True,
        },
        "mcc_prediction": GEMINI_RESPONSE,
        "url": "https://example.com",
    }
    mock_gemini.assert_called_once()
    mock_scrape.assert_not_called()


@patch("mcc_classifier.scrape_website")
@patch("mcc_classifier.call_gemini", return_value=GEMINI_RESPONSE)
def test_legacy_classification_endpoint_uses_same_response(
    mock_gemini,
    mock_scrape,
):
    new_response = client.post("/api/mcc/classify", json=REQUEST)
    legacy_response = client.post("/classify", json=REQUEST)

    assert new_response.status_code == 200
    assert legacy_response.status_code == 200
    assert legacy_response.json() == new_response.json()
    assert mock_gemini.call_count == 2
    mock_scrape.assert_not_called()


def test_classification_requires_url_and_mcc():
    response = client.post("/api/mcc/classify", json={})

    assert response.status_code == 422
