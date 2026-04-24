import io
import uuid
from datetime import datetime, timedelta, timezone
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.storage_service import app, files_metadata, files_content
#from src.storage_service import

print("CONFIGS_LOADED")

@pytest.fixture(scope="session")
def api_client():
    """
    Shared API client for all tests.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def unique_file_name():
    """
    Generates a unique file name for each test.
    """
    return f"test-file-{uuid.uuid4().hex}.bin"


@pytest.fixture
def file_factory():
    """
    Returns a helper that builds an in-memory multipart file payload.
    """

    def _make_file(size_bytes: int, name: str = "test.bin", content_byte: bytes = b"a"):
        if len(content_byte) != 1:
            raise ValueError("content_byte must be exactly one byte")

        content = content_byte * size_bytes
        return {
            "file": (
                name,
                io.BytesIO(content),
                "application/octet-stream",
            )
        }

    return _make_file


@pytest.fixture
def small_valid_file():
    """
    Example valid file above the minimum tiering threshold.
    """
    return b"a" * (512 * 1024)

@pytest.fixture()
def valid_file_bytes():
    """
    API requires at least 1 MB
    """
    return b"a" * (1024 * 1024)

@pytest.fixture
def zero_byte_file():
    """
    0-byte file payload.
    """
    return b""


@pytest.fixture
def just_under_1mb_file(file_factory):
    """
    File just under 1 MB.
    """
    return file_factory((1024 * 1024) - 1, name="under-1mb.bin")


@pytest.fixture
def exactly_1mb_file(file_factory):
    """
    File exactly 1 MB.
    """
    return file_factory(1024 * 1024, name="exactly-1mb.bin")


@pytest.fixture
def upload_file(api_client):
    """
    Upload helper. Returns parsed JSON on success.
    """

    def _upload(file_payload):
        response = api_client.post("/files", files=file_payload)
        assert response.status_code in (200, 201), (
            f"Upload failed. status={response.status_code}, body={response.text}"
        )
        return response.json()

    return _upload


@pytest.fixture
def uploaded_file(api_client, valid_file_bytes):
    """
    Uploads one valid file and returns the response JSON.
    """
    response = api_client.post(
        "/files",
        files={
            "file": (
                "valid-file.bin",
                valid_file_bytes,
                "application/octet-stream",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def uploaded_file_id(uploaded_file):
    """
    Convenience fixture returning only the file id.
    """
    return uploaded_file["file_id"]


@pytest.fixture
def get_metadata(api_client):
    """
    Metadata fetch helper.
    """

    def _get(file_id: str):
        return api_client.get(f"/files/{file_id}/metadata")

    return _get


@pytest.fixture
def download_file(api_client):
    """
    Download helper.
    """

    def _download(file_id: str):
        return api_client.get(f"/files/{file_id}")

    return _download


@pytest.fixture
def delete_file(api_client):
    """
    Delete helper.
    """

    def _delete(file_id: str):
        return api_client.delete(f"/files/{file_id}")

    return _delete


@pytest.fixture
def run_tiering(api_client):
    """
    Manual tiering trigger helper.
    """

    def _run():
        return api_client.post("/admin/tiering/run")

    return _run


@pytest.fixture
def get_stats(api_client):
    """
    Admin stats helper.
    """

    def _stats():
        return api_client.get("/admin/stats")

    return _stats


@pytest.fixture
def age_file():
    """
    Artificially ages a file by changing last_accessed."""

    def _age(file_id, days_old):
        target_time = datetime.utcnow() - timedelta(days=days_old)


        if file_id not in files_metadata:
            raise KeyError(f"File {file_id} not found")

        files_metadata[file_id].last_accessed = target_time

    return _age


@pytest.fixture
def set_file_tier():
    """
    Forces a tier for setup-heavy tests.
    """
    def _set(file_id: str, tier: str):
        if file_id not in files_metadata:
            raise KeyError(f"File {file_id} not found")

        files_metadata[file_id]["tier"] = tier

        raise NotImplementedError("Hook this into the repo's tier field")

    return _set

@pytest.fixture
def unsafe_client():
    """
    Client that converts unhandled server exceptions into HTTP 500 responses,
    which is useful for fault injection tests.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_storage_state():
    """
    Ensures test cleanup.
    """

    files_metadata.clear()
    files_content.clear()
    yield
    files_metadata.clear()
    files_content.clear()