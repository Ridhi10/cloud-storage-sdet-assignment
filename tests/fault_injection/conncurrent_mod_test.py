import threading
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import src.storage_service as storage_service
from src.storage_service import app, files_metadata, files_content, StorageTier
from tests.conftest import *
def test_concurrent_delete_during_download_results_in_failure(
    unsafe_client, uploaded_file_id, monkeypatch
):
    """
    Simulate a race where content disappears while download is in progress.
    """

    start_read = threading.Event()
    allow_continue = threading.Event()

    original_content = storage_service.files_content[uploaded_file_id]

    class BlockingContentStore(dict):
        def __getitem__(self, key):
            start_read.set()
            allow_continue.wait(timeout=2)
            return super().__getitem__(key)

    monkeypatch.setattr(
        storage_service,
        "files_content",
        BlockingContentStore({uploaded_file_id: original_content}),
    )

    result = {}

    def do_download():
        resp = unsafe_client.get(f"/files/{uploaded_file_id}")
        result["status_code"] = resp.status_code

    thread = threading.Thread(target=do_download)
    thread.start()

    assert start_read.wait(timeout=2), "download did not reach content read phase"

    # Simulate concurrent delete / modification
    storage_service.files_content.pop(uploaded_file_id, None)

    allow_continue.set()
    thread.join(timeout=3)

    assert result["status_code"] == 500


def test_concurrent_metadata_corruption_during_tiering_returns_500(
    unsafe_client, uploaded_file_id, monkeypatch
):
    """
    Simulate metadata being modified while tiering is running.
    """
    original_apply = storage_service.apply_special_rules
    has_corrupted = {"done": False}

    def corrupting_apply_special_rules(metadata):
        if not has_corrupted["done"]:
            metadata.last_accessed = "corrupted-by-concurrent-writer"
            has_corrupted["done"] = True
        return original_apply(metadata)

    monkeypatch.setattr(
        storage_service,
        "apply_special_rules",
        corrupting_apply_special_rules,
    )

    response = unsafe_client.post("/admin/tiering/run")

    assert response.status_code == 500
