import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

# TODO: replace these imports with the exact names from the repo
from src.storage_service import app
# from src.storage_service import <your_storage_object>


@pytest.fixture(scope="session")
def api_client():
    """
    Shared API client for all tests.
    """
    # TODO:
    # with TestClient(app) as client:
    #     yield client
    raise NotImplementedError("Wire this fixture to the repo's FastAPI app")


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
def small_valid_file(file_factory):
    """
    Example valid file above the minimum tiering threshold.
    """
    return file_factory(2 * 1024 * 1024, name="small-valid.bin")


@pytest.fixture
def zero_byte_file(file_factory):
    """
    0-byte file payload.
    """
    return file_factory(0, name="zero-byte.bin")


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
def uploaded_file(api_client, small_valid_file):
    """
    Uploads one valid file and returns the response JSON.
    """
    response = api_client.post("/files", files=small_valid_file)
    assert response.status_code in (200, 201), response.text
    return response.json()


@pytest.fixture
def uploaded_file_id(uploaded_file):
    """
    Convenience fixture returning only the file id.
    """
    # TODO: change the key if the API returns a different field name
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
    Artificially ages a file by changing last_accessed.

    TODO:
    - import the actual storage/backend object from the repo
    - update the internal object path and field names
    """

    def _age(file_id: str, days_old: int):
        target_time = datetime.now(timezone.utc) - timedelta(days=days_old)

        # Example only — replace with real repo structure:
        # if file_id not in storage_engine.files:
        #     raise KeyError(f"File {file_id} not found")
        #
        # storage_engine.files[file_id]["last_accessed"] = target_time

        raise NotImplementedError("Hook this into the repo's in-memory storage structure")

    return _age


@pytest.fixture
def set_file_tier():
    """
    Forces a tier for setup-heavy tests.

    TODO:
    - wire to the real backend object
    - replace the field access with the repo's actual storage structure
    """

    def _set(file_id: str, tier: str):
        # Example only:
        # if file_id not in storage_engine.files:
        #     raise KeyError(f"File {file_id} not found")
        #
        # storage_engine.files[file_id]["tier"] = tier

        raise NotImplementedError("Hook this into the repo's tier field")

    return _set


@pytest.fixture(autouse=True)
def clean_storage_state():
    """
    Ensures test isolation.

    TODO:
    - replace with the repo's real cleanup/reset mechanism
    """

    # Example only:
    # storage_engine.files.clear()
    yield
    # storage_engine.files.clear()