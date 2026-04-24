
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tests.conftest import api_client

import pytest
import json

NUM_FILES = 100
FILE_SIZE_MB = 2
MAX_WORKERS = 10


def upload_test_file(api_client, index):
    """
    Upload a single eligible file and return fileId.
    """
    payload = b"x" * (FILE_SIZE_MB * 1024 * 1024)

    response = api_client.post(
        "/files",
        files={
            "file": (
                f"tier_test_file_{index}.bin",
                payload
            )
        }
    )

    assert response.status_code == 201
    return response.json()["file_id"]


# def mark_file_as_old(mocker, days_old):
#     """
#     Mock storage timestamp lookup to simulate stale files.
#     """
#     response = api_client.post()
#     stale_timestamp = time.time() - (days_old * 24 * 60 * 60)
#
#     mocker.patch(
#         "src.storage_service.update_last_accessed",
#         return_value=stale_timestamp
#     )

def mark_file_as_old(api_client, file_id, days_old):
    response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={"days_ago": days_old},
    )
    assert response.status_code == 200

@pytest.mark.performance
def test_tiering_benchmark_100_files(api_client, mocker):
    """
    Benchmark tiering performance for 100 files.

    Scenario:
    - Upload 100 files in parallel
    - Simulate files older than 31 days
    - Run tiering
    - Measure total execution time
    - Verify all files moved to WARM tier
    """

    uploaded_file_ids = []

    upload_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(upload_test_file, api_client, i)
            for i in range(NUM_FILES)
        ]

        for future in as_completed(futures):
            uploaded_file_ids.append(future.result())

    upload_duration = time.perf_counter() - upload_start

    print(f"\nUploaded {NUM_FILES} files in {upload_duration:.2f} sec")
    print(f"Average upload rate: {NUM_FILES / upload_duration:.2f} files/sec")

    # Simulate all files being inactive for more than 30 days
    for file_id in uploaded_file_ids:
        mark_file_as_old(api_client, file_id, days_old=31)

    tiering_start = time.perf_counter()

    tiering_response = api_client.post("/admin/tiering/run")

    tiering_duration = time.perf_counter() - tiering_start

    assert tiering_response.status_code == 200

    print(f"Tiering completed in {tiering_duration:.2f} sec")
    print(f"Tiering throughput: {NUM_FILES / tiering_duration:.2f} files/sec")

    failed_files = []

    for file_id in uploaded_file_ids:
        metadata_response = api_client.get(f"/files/{file_id}/metadata")

        assert metadata_response.status_code == 200

        metadata = metadata_response.json()

        if metadata["tier"] != "WARM":
            failed_files.append(file_id)

    assert len(failed_files) == 0, (
        f"{len(failed_files)} files did not move to WARM tier"
    )

    assert tiering_duration < 30, (
        f"Tiering took too long: {tiering_duration:.2f} sec"
    )

    print(f"All {NUM_FILES} files successfully moved to WARM tier")


@pytest.mark.performance
def test_repeated_tiering_run_is_idempotent(api_client, mocker):
    """
    Verify repeated tiering runs do not reprocess files unnecessarily.
    """

    file_id = upload_test_file(api_client, 1)

    mark_file_as_old(api_client, file_id, days_old=31)

    first_run = api_client.post("/admin/tiering/run")
    assert first_run.status_code == 200

    metadata_after_first_run = api_client.get(
        f"/files/{file_id}/metadata"
    ).json()

    assert metadata_after_first_run["tier"] == "WARM"

    second_run_start = time.perf_counter()

    second_run = api_client.post("/admin/tiering/run")

    second_run_duration = time.perf_counter() - second_run_start

    assert second_run.status_code == 200

    metadata_after_second_run = api_client.get(
        f"/files/{file_id}/metadata"
    ).json()

    assert metadata_after_second_run["tier"] == "WARM"

    assert second_run_duration < 10, (
        f"Repeated tiering run too slow: {second_run_duration:.2f} sec"
    )

    print(f"Repeated tiering completed in {second_run_duration:.2f} sec")


@pytest.mark.performance
def test_tiering_under_parallel_admin_requests(api_client, mocker):
    """
    Verify system remains stable when multiple tiering requests
    are triggered simultaneously.
    """

    uploaded_file_ids = []

    for i in range(20):
        uploaded_file_ids.append(upload_test_file(api_client, i))

    for file_id in uploaded_file_ids:
        mark_file_as_old(api_client, file_id, days_old=31)

    def trigger_tiering():
        return api_client.post("/admin/tiering/run")

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(trigger_tiering)
            for _ in range(5)
        ]

        responses = [future.result() for future in futures]

    duration = time.perf_counter() - start

    assert all(response.status_code == 200 for response in responses)

    for file_id in uploaded_file_ids:
        metadata = api_client.get(
            f"/files/{file_id}/metadata"
        ).json()

        assert metadata["tier"] == "WARM"

    assert duration < 20, (
        f"Concurrent tiering requests took too long: {duration:.2f} sec"
    )

    print(f"Parallel tiering requests completed in {duration:.2f} sec")