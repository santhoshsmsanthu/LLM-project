
import pytest
from unittest.mock import patch

import job_processor as jp


@pytest.fixture(autouse=True)
def reset_running():
    with jp.lock:
        jp.running.clear()

    yield

    with jp.lock:
        jp.running.clear()


def test_duplicate_job():
    with jp.lock:
        jp.running.add("unique-123")

    with pytest.raises(jp.DuplicateJob) as exc:
        jp.submit_job("job-1", "unique-123", {})

    assert exc.value.status_code == 409


def test_queue_full():
    original_limit = jp.settings.MAX_QUEUED_JOBS

    try:
        jp.settings.MAX_QUEUED_JOBS = 40

        with jp.lock:
            jp.running.update(
                f"unique-{i}" for i in range(40)
            )

        with pytest.raises(jp.QueueFull) as exc:
            jp.submit_job("job-41", "unique-41", {})

        assert exc.value.status_code == 503

    finally:
        jp.settings.MAX_QUEUED_JOBS = original_limit


@patch("job_processor.executor.submit")
def test_successful_submission(mock_submit):
    mock_submit.return_value = "fake-future"

    result = jp.submit_job(
        "job-1",
        "unique-1",
        {},
    )

    assert result == "fake-future"
    assert "unique-1" in jp.running
    mock_submit.assert_called_once()


@patch("job_processor.save_success")
@patch("job_processor.classify")
def test_process_success(mock_classify, mock_save_success):
    mock_classify.return_value = {
        "url": "https://example.com",
        "mcc_response": {"mcc_match": True},
    }

    jp._process(
        "job-1",
        "unique-1",
        {"url": "https://example.com"},
    )

    mock_save_success.assert_called_once()
    assert "unique-1" not in jp.running


@patch("job_processor.save_failure")
@patch("job_processor.classify")
def test_process_failure(mock_classify, mock_save_failure):
    mock_classify.side_effect = Exception(
        "Classification failed"
    )

    with jp.lock:
        jp.running.add("unique-2")

    jp._process(
        "job-2",
        "unique-2",
        {"url": "https://example.com"},
    )

    mock_save_failure.assert_called_once()
    assert "unique-2" not in jp.running


def test_running_cleanup_when_save_success_fails():
    with patch(
        "job_processor.classify",
        return_value={"result": "ok"},
    ), patch(
        "job_processor.save_success",
        side_effect=Exception("Database error"),
    ), patch(
        "job_processor.save_failure"
    ) as mock_save_failure:

        with jp.lock:
            jp.running.add("unique-3")

        jp._process(
            "job-3",
            "unique-3",
            {"url": "https://example.com"},
        )

        mock_save_failure.assert_called_once()
        assert "unique-3" not in jp.running
