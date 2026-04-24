import threading
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import src.storage_service as storage_service
from src.storage_service import app, files_metadata, files_content, StorageTier
from tests.conftest import *
def test_corrupted_last_accessed_type_causes_tiering_failure(
    unsafe_client, uploaded_file_id
):
    """
    Corrupt datetime field used by tiering logic.
    """
    files_metadata[uploaded_file_id].last_accessed = "not-a-datetime"

    response = unsafe_client.post("/admin/tiering/run")

    assert response.status_code == 500


def test_corrupted_invalid_tier_value_causes_tiering_failure(
    unsafe_client, uploaded_file_id
):
    """
    Corrupt tier so TIER_CONFIG lookup fails.
    """
    files_metadata[uploaded_file_id].tier = "BROKEN_TIER"

    response = unsafe_client.post("/admin/tiering/run")

    assert response.status_code == 500


def test_corrupted_size_type_breaks_stats_endpoint(
    unsafe_client, uploaded_file_id
):
    """
    Corrupt file size so stats aggregation fails.
    """
    files_metadata[uploaded_file_id].size = "1MB"

    response = unsafe_client.get("/admin/stats")

    assert response.status_code == 500


def test_corrupted_missing_metadata_but_content_exists_returns_404(
    api_client, uploaded_file_id
):
    """
    Simulate inverse corruption: content exists but metadata is missing.
    API checks metadata first, so it should return 404.
    """
    storage_service.files_metadata.pop(uploaded_file_id, None)

    response = api_client.get(f"/files/{uploaded_file_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"