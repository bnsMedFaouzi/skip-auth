import pytest


# ===========================================================================
# ProviderSource
# ===========================================================================

def test_provider_source_requires_all_fields():
    from data_push_cft.output_platform.internal.schemas.publication import ProviderSource
    with pytest.raises(Exception):
        ProviderSource()


def test_provider_source_fields_assigned():
    from data_push_cft.output_platform.internal.schemas.publication import ProviderSource
    ps = ProviderSource(idf="IDF1", part="PART1", cftname="CFT1")
    assert ps.idf == "IDF1"
    assert ps.part == "PART1"
    assert ps.cftname == "CFT1"


# ===========================================================================
# EventFromCft
# ===========================================================================

def _valid_event(**kwargs):
    from data_push_cft.output_platform.internal.schemas.publication import (
        EventFromCft, ProviderSource
    )
    defaults = {
        "filename": "test.txt",
        "provider_source": ProviderSource(idf="IDF1", part="PART1", cftname="CFT1"),
        "bucket_name": "my-bucket",
        "bucket_endpoint": "https://cos.example.com",
        "ecosystem": "prod",
    }
    defaults.update(kwargs)
    return EventFromCft(**defaults)


def test_event_from_cft_requires_all_fields():
    from data_push_cft.output_platform.internal.schemas.publication import EventFromCft
    with pytest.raises(Exception):
        EventFromCft()


def test_event_from_cft_filename_min_length_one():
    with pytest.raises(Exception):
        _valid_event(filename="")


def test_event_from_cft_origin_defaults_to_none():
    event = _valid_event()
    assert event.origin is None


def test_event_from_cft_origin_accepts_dict():
    event = _valid_event(origin={"key": "value"})
    assert event.origin == {"key": "value"}


def test_event_from_cft_bucket_endpoint_is_validated_url():
    with pytest.raises(Exception):
        _valid_event(bucket_endpoint="not-a-url")


def test_event_from_cft_fields_assigned():
    event = _valid_event()
    assert event.filename == "test.txt"
    assert event.bucket_name == "my-bucket"
    assert event.ecosystem == "prod"


def test_event_from_cft_provider_source_assigned():
    from data_push_cft.output_platform.internal.schemas.publication import ProviderSource
    ps = ProviderSource(idf="IDF1", part="PART1", cftname="CFT1")
    event = _valid_event(provider_source=ps)
    assert event.provider_source is ps
