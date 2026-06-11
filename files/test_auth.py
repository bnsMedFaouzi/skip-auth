import pytest
from unittest.mock import MagicMock


# ===========================================================================
# Helpers
# ===========================================================================

def _valid_file_location(**kwargs):
    from data_push_cft.output_platform.internal.schemas.publisher import FileLocation
    defaults = {
        "bucket_name": "my-bucket",
        "bucket_endpoint": "https://cos.example.com",
        "cos": "my-cos",
        "ecosystem": "prod",
    }
    defaults.update(kwargs)
    return FileLocation.model_validate(defaults)


def _valid_publisher_request_body(**kwargs):
    from data_push_cft.output_platform.internal.schemas.publisher import (
        PublisherRequestBody, Metadata
    )
    metadata = Metadata.model_construct(
        pivots=[MagicMock()],
        metadata_filename="meta.json"
    )
    defaults = {
        "metadata": metadata,
        "publication_type": MagicMock(),
        "file_location": _valid_file_location(),
    }
    defaults.update(kwargs)
    return PublisherRequestBody(**defaults)


# ===========================================================================
# FileLocation
# ===========================================================================

def test_file_location_requires_all_fields():
    from data_push_cft.output_platform.internal.schemas.publisher import FileLocation
    with pytest.raises(Exception):
        FileLocation()


def test_file_location_bucket_alias():
    loc = _valid_file_location()
    assert loc.bucket == "my-bucket"


def test_file_location_endpoint_alias():
    loc = _valid_file_location()
    assert "cos.example.com" in str(loc.endpoint)


def test_file_location_endpoint_validates_url():
    with pytest.raises(Exception):
        _valid_file_location(bucket_endpoint="not-a-url")


def test_file_location_cos_and_ecosystem_assigned():
    loc = _valid_file_location()
    assert loc.cos == "my-cos"
    assert loc.ecosystem == "prod"


# ===========================================================================
# Metadata
# ===========================================================================

def test_metadata_requires_pivots_and_filename():
    from data_push_cft.output_platform.internal.schemas.publisher import Metadata
    with pytest.raises(Exception):
        Metadata()


def test_metadata_pivots_min_length_one():
    from data_push_cft.output_platform.internal.schemas.publisher import Metadata
    with pytest.raises(Exception):
        Metadata.model_validate({"pivots": [], "metadata_filename": "meta.json"})


def test_metadata_fields_assigned():
    from data_push_cft.output_platform.internal.schemas.publisher import Metadata
    mock_pivot = MagicMock()
    m = Metadata.model_construct(pivots=[mock_pivot], metadata_filename="meta.json")
    assert m.metadata_filename == "meta.json"
    assert len(m.pivots) == 1


# ===========================================================================
# PublisherRequestBody
# ===========================================================================

def test_publisher_request_body_requires_all_fields():
    from data_push_cft.output_platform.internal.schemas.publisher import PublisherRequestBody
    with pytest.raises(Exception):
        PublisherRequestBody()


def test_publisher_request_body_is_deleted_defaults_to_false():
    body = _valid_publisher_request_body()
    assert body.is_deleted is False


def test_publisher_request_body_is_deleted_can_be_true():
    body = _valid_publisher_request_body(is_deleted=True)
    assert body.is_deleted is True


def test_publisher_request_body_fields_assigned():
    loc = _valid_file_location()
    body = _valid_publisher_request_body(file_location=loc)
    assert body.file_location is loc
