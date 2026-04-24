from src.storage_service import StorageTier
from tests.conftest import *

def test_delete_existing_file_returns_204(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    response = api_client.delete(f"/files/{file_id}")

    assert response.status_code == 204
    assert response.text == ""


def test_deleted_file_metadata_returns_404(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    delete_response = api_client.delete(f"/files/{file_id}")
    assert delete_response.status_code == 204

    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 404
    assert metadata_response.json()["detail"] == "File not found"



def test_delete_nonexistent_file_returns_404(api_client):
    response = api_client.delete("/files/nonexistent-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"

def test_delete_updates_stats(api_client, valid_file_bytes):
    upload_response = api_client.post(
        "/files",
        files={
            "file": (
                "stats-check.bin",
                valid_file_bytes,
                "application/octet-stream",
            )
        },
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]
    uploaded_size = upload_response.json()["size"]

    stats_after_upload = api_client.get("/admin/stats")
    assert stats_after_upload.status_code == 200
    upload_stats = stats_after_upload.json()

    assert upload_stats["total_files"] == 1
    assert upload_stats["total_size"] == uploaded_size

    delete_response = api_client.delete(f"/files/{file_id}")
    assert delete_response.status_code == 204

    stats_after_delete = api_client.get("/admin/stats")
    assert stats_after_delete.status_code == 200
    delete_stats = stats_after_delete.json()

    assert delete_stats["total_files"] == 0
    assert delete_stats["total_size"] == 0

