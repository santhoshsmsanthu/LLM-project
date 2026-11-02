
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mongo_store


def setup_function():
    mongo_store._client = None


def teardown_function():
    mongo_store._client = None


@patch("mongo_store.MongoClient")
def test_get_db(mock_mongo_client):
    mock_client = MagicMock()
    mock_mongo_client.return_value = mock_client

    db = mongo_store.get_db()

    mock_mongo_client.assert_called_once()
    mock_client.__getitem__.assert_called_with("MFApiServices")


@patch("mongo_store.get_db")
def test_save_success(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_db["llm_mcc_pred_api"].replace_one.return_value = (
        SimpleNamespace(
            matched_count=0,
            modified_count=0,
            upserted_id="https://example.com_job-1",
        )
    )

    mock_db["job_schedule_api"].update_one.return_value = (
        SimpleNamespace(
            matched_count=1,
            modified_count=1,
        )
    )

    result = {
        "url": "https://example.com",
        "mcc_response": {
            "claimed_mcc": "5732",
            "predicted_mcc": "5732",
            "mcc_match": True,
        },
    }

    document = mongo_store.save_success(
        "job-1",
        "unique-1",
        result,
    )

    assert document["_id"] == "https://example.com_job-1"
    assert document["url"] == "https://example.com"
    assert document["item"]["Payload"] == result

    mock_db["llm_mcc_pred_api"].replace_one.assert_called_once_with(
        {"_id": "https://example.com_job-1"},
        document,
        upsert=True,
    )

    mock_db["job_schedule_api"].update_one.assert_called_once_with(
        {
            "job_id": "job-1",
            "unique_id": "unique-1",
        },
        {
            "$set": {
                "status": 3,
            }
        },
    )


@patch("mongo_store.get_db")
def test_save_success_rejects_missing_url(mock_get_db):
    import pytest

    with pytest.raises(ValueError):
        mongo_store.save_success(
            "job-1",
            "unique-1",
            {"mcc_response": {}},
        )

    mock_get_db.assert_not_called()
