from datetime import datetime

from src.storage_service import StorageTier
from tests.conftest import *

def test_download_existing_file_returns_content_and_metadata(api_client, uploaded_file, valid_file_bytes):
    file_id = uploaded_file["file_id"]

    response = api_client.get(f"/files/{file_id}")

    assert response.status_code == 200

    body = response.json()
    assert body["filename"] == "valid-file.bin"
    assert body["content_type"] == "application/octet-stream"

    # FastAPI JSON-encodes bytes, so content comes back as a string
    assert body["content"] == valid_file_bytes.decode("utf-8")


def test_download_nonexistent_file_returns_404(api_client):
    response = api_client.get("/files/nonexistent-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_download_updates_last_accessed_timestamp(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    before_metadata = api_client.get(f"/files/{file_id}/metadata").json()
    before_last_accessed = datetime.fromisoformat(before_metadata["last_accessed"])

    response = api_client.get(f"/files/{file_id}")
    assert response.status_code == 200

    after_metadata = api_client.get(f"/files/{file_id}/metadata").json()
    after_last_accessed = datetime.fromisoformat(after_metadata["last_accessed"])

    assert after_last_accessed >= before_last_accessed

def test_download_succeeds_regardless_of_tier(
    api_client, uploaded_file, age_file, run_tiering
):
    file_id = uploaded_file["file_id"]

    # HOT download
    hot_download = api_client.get(f"/files/{file_id}")
    assert hot_download.status_code == 200

    # HOT -> WARM
    age_file(file_id, 31)
    assert run_tiering().status_code == 200

    warm_metadata = api_client.get(f"/files/{file_id}/metadata").json()
    assert warm_metadata["tier"] == "WARM"

    warm_download = api_client.get(f"/files/{file_id}")
    assert warm_download.status_code == 200

    # WARM -> COLD
    age_file(file_id, 91)
    assert run_tiering().status_code == 200

    cold_metadata = api_client.get(f"/files/{file_id}/metadata").json()
    assert cold_metadata["tier"] == "COLD"

    cold_download = api_client.get(f"/files/{file_id}")
    assert cold_download.status_code == 200
