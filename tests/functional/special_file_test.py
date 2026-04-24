from src.storage_service import StorageTier, files_metadata, files_content, app, apply_special_rules, FileMetadata
from tests.conftest import *




def test_apply_special_rules_priority_file_forces_hot():
    metadata = FileMetadata(
        file_id="1",
        filename="report_PRIORITY_backup.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=120),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) == StorageTier.HOT

def test_apply_special_rules_priority_file_is_case_insensitive():
    metadata = FileMetadata(
        file_id="1",
        filename="report_priority_backup.pdf",
        size=1024 * 1024,
        tier=StorageTier.COLD,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=200),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) == StorageTier.HOT

def test_apply_special_rules_legal_file_in_warm_within_180_days_stays_warm():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL_contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=100),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) == StorageTier.WARM

def test_apply_special_rules_legal_file_exactly_180_days_stays_warm():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL_contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=180),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) == StorageTier.WARM

def test_apply_special_rules_legal_file_over_180_days_returns_none():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL_contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=181),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) is None

def test_apply_special_rules_legal_file_in_hot_returns_none():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL_contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.HOT,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=100),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) is None


def test_apply_special_rules_legal_file_in_cold_returns_none():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL_contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.COLD,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=100),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) is None


def test_apply_special_rules_regular_file_returns_none():
    metadata = FileMetadata(
        file_id="1",
        filename="normal_report.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=100),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) is None

def test_apply_special_rules_priority_takes_precedence_over_legal():
    metadata = FileMetadata(
        file_id="1",
        filename="LEGAL__PRIORITY__contract.pdf",
        size=1024 * 1024,
        tier=StorageTier.WARM,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow() - timedelta(days=50),
        content_type="application/pdf",
        etag="abc",
    )

    assert apply_special_rules(metadata) == StorageTier.HOT