from src.storage_service import StorageTier
from tests.conftest import *

@pytest.mark.manual
@pytest.mark.xfail(reason="Known bug: COLD files are not promoted after recent access")
def test_cold_file_should_promote_to_warm_after_recent_access(api_client):
    """
    Requirement validation:
    Recently accessed COLD files should move back toward warmer tiers.

    Expected:
    COLD -> WARM after file access + tiering run

    Current implementation:
    File remains COLD, so this test should fail.
    """

    # Step 1: Upload valid eligible file
    upload_response = api_client.post(
        "/files",
        files={
            "file": (
                "cold_promotion_test.bin",
                b"x" * (2 * 1024 * 1024)  # 2 MB
            )
        }
    )

    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]

    # Step 2: Make file old enough to move HOT -> WARM
    update_response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={"days_ago": 31}
    )
    assert update_response.status_code == 200

    tiering_response = api_client.post("/admin/tiering/run")
    assert tiering_response.status_code == 200

    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200
    assert metadata_response.json()["tier"] == "WARM"

    # Step 3: Make WARM file old enough to move WARM -> COLD
    update_response = api_client.post(
        f"/admin/files/{file_id}/update-last-accessed",
        json={"days_ago": 91}
    )
    assert update_response.status_code == 200

    tiering_response = api_client.post("/admin/tiering/run")
    assert tiering_response.status_code == 200

    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200
    assert metadata_response.json()["tier"] == "COLD"

    # Step 4: Access/download the COLD file
    download_response = api_client.get(f"/files/{file_id}")
    assert download_response.status_code == 200

    # Step 5: Run tiering again after recent access
    tiering_response = api_client.post("/admin/tiering/run")
    assert tiering_response.status_code == 200

    # Step 6: Validate expected promotion
    metadata_response = api_client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200

    metadata = metadata_response.json()

    assert metadata["tier"] == "WARM", (
        "Expected recently accessed COLD file to be promoted to WARM, "
        f"but actual tier is {metadata['tier']}"
    )