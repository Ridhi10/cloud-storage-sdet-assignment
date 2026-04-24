import threading
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import src.storage_service as storage_service
from src.storage_service import app, files_metadata, files_content, StorageTier
from tests.conftest import *
def test_storage_read_failure_during_download_returns_500(
    unsafe_client, uploaded_file_id, monkeypatch
):
    """
    Simulate backend/storage read failure when downloading content.
    """

    class FailingContentStore(dict):
        def __getitem__(self, key):
            raise IOError("disk read failed")

    monkeypatch.setattr(storage_service, "files_content", FailingContentStore(files_content))

    response = unsafe_client.get(f"/files/{uploaded_file_id}")

    assert response.status_code == 500


def test_storage_write_failure_during_upload_returns_500(
    unsafe_client, monkeypatch
):
    """
    Simulate backend/storage write failure while saving file content.
    The current implementation writes metadata first and content second,
    so this test validates failure visibility, not rollback.
    """

    class FailingContentStore(dict):
        def __setitem__(self, key, value):
            raise IOError("disk write failed")

    before_meta = len(files_metadata)
    before_content = len(files_content)

    monkeypatch.setattr(storage_service, "files_content", FailingContentStore())

    response = unsafe_client.post(
        "/files",
        files={
            "file": (
                "storage-write-failure.bin",
                b"a" * (1024 * 1024),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 500

    # Current service does not roll back metadata on content write failure.
    # This assertion documents current behavior so the test remains aligned
    # with the implementation.
    assert len(files_metadata) == before_meta + 1
    assert len(storage_service.files_content) == before_content


def test_storage_backend_missing_content_for_existing_metadata_returns_500(
    unsafe_client, uploaded_file_id
):
    """
    Simulate storage inconsistency: metadata exists, binary content missing.
    """
    storage_service.files_content.pop(uploaded_file_id, None)

    response = unsafe_client.get(f"/files/{uploaded_file_id}")

    assert response.status_code == 500

