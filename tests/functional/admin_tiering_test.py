import pytest

from src.storage_service import StorageTier
from tests.conftest import *

def test_run_tiering_moves_hot_file_to_warm(api_client, uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)

    response = run_tiering()
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert "files_moved" in body
    assert body["files_moved"] >= 1

    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()

    assert metadata["tier"] == "WARM"


def test_run_tiering_moves_warm_file_to_cold(api_client, uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)
    first_response = run_tiering()
    assert first_response.status_code == 200

    metadata_after_first_run = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata_after_first_run["tier"] == "WARM"

    age_file(file_id, 91)
    second_response = run_tiering()
    assert second_response.status_code == 200

    metadata_after_second_run = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata_after_second_run["tier"] == "COLD"


def test_run_tiering_does_not_move_recent_hot_file(api_client, uploaded_file, run_tiering):
    file_id = uploaded_file["file_id"]

    response = run_tiering()
    assert response.status_code == 200

    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()

    assert metadata["tier"] == "HOT"


def test_run_tiering_is_idempotent_for_already_tiered_file(api_client, uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)

    first_response = run_tiering()
    assert first_response.status_code == 200

    metadata_after_first = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata_after_first["tier"] == "WARM"

    second_response = run_tiering()
    assert second_response.status_code == 200

    metadata_after_second = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata_after_second["tier"] == "WARM"


def test_run_tiering_processes_multiple_files(api_client, upload_file, file_factory, age_file, run_tiering):
    uploaded = []

    for i in range(3):
        response_json = upload_file(
            file_factory(1024 * 1024, name=f"file-{i}.bin")
        )
        uploaded.append(response_json["file_id"])

    for file_id in uploaded:
        age_file(file_id, 31)

    response = run_tiering()
    assert response.status_code == 200

    for file_id in uploaded:
        metadata = api_client.get(f"/files/{file_id}/metadata").json()
        assert metadata["tier"] == "WARM"


def test_run_tiering_returns_expected_response_fields(uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)

    response = run_tiering()
    assert response.status_code == 200

    body = response.json()
    assert "status" in body
    assert "files_moved" in body
    assert body["status"] == "success"
    assert isinstance(body["files_moved"], int)
    assert body["files_moved"] == 1