import threading
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import src.storage_service as storage_service
from src.storage_service import app, files_metadata, files_content, StorageTier
from tests.conftest import *

def test_network_failure_during_upload_returns_500_and_does_not_store_file(
    unsafe_client, monkeypatch
):
    """
    Simulate client/network disconnect while server is reading upload body.
    """
    before_meta = len(files_metadata)
    before_content = len(files_content)

    async def broken_read(self):
        raise ConnectionResetError("client disconnected during upload")

    monkeypatch.setattr("starlette.datastructures.UploadFile.read", broken_read)

    response = unsafe_client.post(
        "/files",
        files={
            "file": (
                "network-failure.bin",
                b"a" * (1024 * 1024),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 500
    assert len(files_metadata) == before_meta
    assert len(files_content) == before_content


def test_network_timeout_during_upload_returns_500_and_does_not_store_file(
    unsafe_client, monkeypatch
):
    """
    Simulate timeout while reading request body.
    """
    before_meta = len(files_metadata)
    before_content = len(files_content)

    async def timeout_read(self):
        raise TimeoutError("upload timed out")

    monkeypatch.setattr("starlette.datastructures.UploadFile.read", timeout_read)

    response = unsafe_client.post(
        "/files",
        files={
            "file": (
                "timeout.bin",
                b"a" * (1024 * 1024),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 500
    assert len(files_metadata) == before_meta
    assert len(files_content) == before_content

