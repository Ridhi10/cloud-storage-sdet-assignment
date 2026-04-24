from src.storage_service import StorageTier
from tests.conftest import *

def test_upload_valid_file_returns_201_and_metadata(api_client, valid_file_bytes):
    response = api_client.post(
        "/files",
        files ={
            "file": (
                "valid-file.bin",
                valid_file_bytes,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "file_id" in body
    assert body["filename"] == "valid-file.bin"
    assert body["size"] == len(valid_file_bytes)
    assert body["tier"] == StorageTier.HOT.value
    assert body["content_type"] == "application/octet-stream"
    assert body["etag"]


def test_upload_file_smaller_than_1mb_returns_400(api_client, small_valid_file):
    #small_payload = b"x" * (1024 * 512)  # 512 KB

    response = api_client.post(
        "/files",
        files={
            "file": (
                "too_small.bin",
                small_valid_file,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File size must be at least 1MB"

@pytest.mark.skip(reason="Avoid allocating 10GB payload in CI")
def test_upload_file_exactly_10gb_returns_201_and_metadata(api_client, valid_file_bytes):
    big_payload = b"x" * (10 * 1024 * 1024 * 1024)  # 10 GB

    response = api_client.post(
        "/files",
        files={
            "file": (
                "large-file.bin",
                big_payload,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "file_id" in body
    assert body["filename"] == "large-file.bin"
    assert body["size"] == len(big_payload)
    assert body["tier"] == StorageTier.HOT.value
    assert body["content_type"] == "application/octet-stream"
    assert body["etag"]

@pytest.mark.skip(reason="Avoid allocating 10GB payload in CI")
def test_upload_file_larger_than_10gb_returns_400(api_client, valid_file_bytes):
    big_payload = b"x" * (11 * 1024 * 1024 * 1024)  # 11 GB

    response = api_client.post(
        "/files",
        files={
            "file": (
                "large-file.bin",
                big_payload,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File size exceeds maximum limit of 10GB"

def test_priority_rule_with_special_characters(api_client, valid_file_bytes, age_file, run_tiering):
    filename = "my _PRIORITY_ file @2026#.bin"

    upload = api_client.post(
        "/files",
        files={"file": (filename, valid_file_bytes, "application/octet-stream")},
    )

    file_id = upload.json()["file_id"]

    age_file(file_id, 100)
    run_tiering()

    metadata = api_client.get(f"/files/{file_id}/metadata").json()

    assert metadata["tier"] == "HOT"

def test_upload_without_content_type_defaults_to_octet_stream(api_client, valid_file_bytes):
    response = api_client.post(
        "/files",
        files={
            "file": (
                "no_type.bin",
                valid_file_bytes,
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == "application/octet-stream"


def test_upload_generates_unique_file_ids(api_client, valid_file_bytes):
    response1 = api_client.post(
        "/files",
        files={"file": ("file1.bin", valid_file_bytes, "application/octet-stream")},
    )
    response2 = api_client.post(
        "/files",
        files={"file": ("file2.bin", valid_file_bytes, "application/octet-stream")},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["file_id"] != response2.json()["file_id"]
    assert response1.json()["size"] == response2.json()["size"] == len(valid_file_bytes)


def test_exactly_1mb_file_can_move_to_warm(api_client, uploaded_file, age_file, run_tiering):
    file_id = uploaded_file["file_id"]

    age_file(file_id, 31)

    assert uploaded_file["size"] == 1024 * 1024

    response = run_tiering()
    assert response.status_code == 200

    metadata = api_client.get(f"/files/{file_id}/metadata").json()
    assert metadata["tier"] == "WARM"


"""Below are a few negative testcases run"""

def test_upload_zero_byte_file_returns_400(api_client, zero_byte_file):
    response = api_client.post(
        "/files",
        files={
            "file": (
                "empty.bin",
                zero_byte_file,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File size must be at least 1MB"

def test_upload_without_file_payload_returns_422(api_client):
    response = api_client.post("/files")

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)

    error_fields = [err["loc"][-1] for err in body["detail"]]
    assert "file" in error_fields


def test_upload_with_different_content_type_returns_201(api_client, valid_file_bytes):
    response = api_client.post(
        "/files",
        files={
            "file": (
                "test.exe",
                valid_file_bytes,
                "application/x-msdownload",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["content_type"] == "application/x-msdownload"


def test_update_last_accessed_for_existing_file_returns_200(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={"days_ago": 31},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["file_id"] == file_id
    assert "last_accessed" in body


def test_update_last_accessed_for_nonexistent_file_returns_404(api_client):
    response = api_client.post(
        "/admin/files/nonexistent-id/update-last-accessed",
        json={"days_ago": 31},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_update_last_accessed_sets_expected_age(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={"days_ago": 10},
    )

    assert response.status_code == 200

    last_accessed = datetime.fromisoformat(response.json()["last_accessed"])
    expected = datetime.utcnow() - timedelta(days=10)

    assert abs((expected - last_accessed).total_seconds()) < 5


""" This is a negative Test"""
def test_update_last_accessed_with_missing_days_ago_returns_422(api_client, uploaded_file):
    file_id = uploaded_file["file_id"]

    response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={},
    )

    assert response.status_code == 422