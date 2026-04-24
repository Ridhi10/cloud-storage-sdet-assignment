from src.storage_service import StorageTier
from tests.conftest import *

def test_get_metadata_for_existing_file(api_client, uploaded_file, valid_file_bytes):
    file_id = uploaded_file["file_id"]

    response = api_client.get(f"/files/{file_id}/metadata")

    assert response.status_code == 200

    body = response.json()
    assert body["file_id"] == file_id
    assert body["filename"] == "valid-file.bin"
    assert body["size"] == len(valid_file_bytes)
    assert body["tier"] == StorageTier.HOT.value
    assert body["content_type"] == "application/octet-stream"
    assert "created_at" in body
    assert "last_accessed" in body
    assert "etag" in body


def test_get_metadata_for_nonexistent_file_returns_404(api_client):
    response = api_client.get("/files/nonexistent-id/metadata")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_metadata_does_not_change_tier_on_read(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    response1 = api_client.get(f"/files/{file_id}/metadata")
    response2 = api_client.get(f"/files/{file_id}/metadata")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["tier"] == "HOT"
    assert response2.json()["tier"] == "HOT"