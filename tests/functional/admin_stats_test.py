
from src.storage_service import StorageTier
from tests.conftest import *

def test_admin_stats_returns_expected_keys(get_stats):
    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert "total_files" in body
    assert "total_size" in body
    assert "tiers" in body

    assert "HOT" in body["tiers"]
    assert "WARM" in body["tiers"]
    assert "COLD" in body["tiers"]

    assert "count" in body["tiers"]["HOT"]
    assert "size" in body["tiers"]["HOT"]

def test_admin_stats_empty_storage(get_stats):
    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert body["total_files"] == 0
    assert body["total_size"] == 0
    assert body["tiers"]["HOT"]["count"] == 0
    assert body["tiers"]["WARM"]["count"] == 0
    assert body["tiers"]["COLD"]["count"] == 0


def test_admin_stats_after_single_upload(get_stats, uploaded_file):
    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert body["total_files"] == 1
    assert body["total_size"] == uploaded_file["size"]
    assert body["tiers"]["HOT"]["count"] == 1
    assert body["tiers"]["WARM"]["count"] == 0
    assert body["tiers"]["COLD"]["count"] == 0


def test_admin_stats_after_multiple_uploads(get_stats, upload_file, file_factory):
    upload_file(file_factory(1024 * 1024, name="file-1.bin"))
    upload_file(file_factory(2 * 1024 * 1024, name="file-2.bin"))
    upload_file(file_factory(3 * 1024 * 1024, name="file-3.bin"))

    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert body["total_files"] == 3
    assert body["total_size"] == (1024 * 1024) + (2 * 1024 * 1024) + (3 * 1024 * 1024)
    assert body["tiers"]["HOT"]["count"] == 3
    assert body["tiers"]["WARM"]["count"] == 0
    assert body["tiers"]["COLD"]["count"] == 0


def test_admin_stats_reflects_tier_changes(api_client, get_stats, uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)
    run_tiering()

    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert body["total_files"] == 1
    assert body["tiers"]["HOT"]["count"] == 0
    assert body["tiers"]["WARM"]["count"] == 1
    assert body["tiers"]["COLD"]["count"] == 0

    metadata = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata["tier"] == "WARM"


def test_admin_stats_updates_after_delete(get_stats, uploaded_file, delete_file):
    file_id = uploaded_file["file_id"]

    delete_response = delete_file(file_id)
    assert delete_response.status_code == 204

    response = get_stats()
    assert response.status_code == 200

    body = response.json()

    assert body["total_files"] == 0
    assert body["total_size"] == 0
    assert body["tiers"]["HOT"]["count"] == 0
    assert body["tiers"]["WARM"]["count"] == 0
    assert body["tiers"]["COLD"]["count"] == 0