import pytest
from unittest.mock import patch

from tests.fixtures.output_platform_fixtures import (
    mock_cft,
    mock_etl,
    mock_internal,
    mock_platforms,
    platform_factory,
)


# ===========================================================================
# PLATFORMS list
# ===========================================================================

def test_platforms_is_list(mock_platforms):
    from data_push_cft.output_platform import PLATFORMS
    assert isinstance(PLATFORMS, list)


def test_platforms_contains_three_entries(mock_platforms):
    from data_push_cft.output_platform import PLATFORMS
    assert len(PLATFORMS) == 3


def test_platforms_contains_cft(mock_platforms):
    from data_push_cft.output_platform import PLATFORMS
    names = [p.__PLATFORM_NAME__ for p in PLATFORMS]
    assert "CFT" in names


def test_platforms_contains_etl(mock_platforms):
    from data_push_cft.output_platform import PLATFORMS
    names = [p.__PLATFORM_NAME__ for p in PLATFORMS]
    assert "ETL" in names


def test_platforms_contains_internal(mock_platforms):
    from data_push_cft.output_platform import PLATFORMS
    names = [p.__PLATFORM_NAME__ for p in PLATFORMS]
    assert "INTERNAL" in names


# ===========================================================================
# platform_by_name dict
# ===========================================================================

def test_platform_by_name_is_dict(mock_platforms):
    from data_push_cft.output_platform import platform_by_name
    assert isinstance(platform_by_name, dict)


def test_platform_by_name_has_cft_key(mock_platforms):
    from data_push_cft.output_platform import platform_by_name
    assert "CFT" in platform_by_name


def test_platform_by_name_has_etl_key(mock_platforms):
    from data_push_cft.output_platform import platform_by_name
    assert "ETL" in platform_by_name


def test_platform_by_name_has_internal_key(mock_platforms):
    from data_push_cft.output_platform import platform_by_name
    assert "INTERNAL" in platform_by_name


def test_platform_by_name_keys_are_uppercased(mock_platforms):
    from data_push_cft.output_platform import platform_by_name
    for key in platform_by_name:
        assert key == key.upper()


# ===========================================================================
# PlatformFactory.__init__
# ===========================================================================

def test_platform_factory_default_platform_is_cft(platform_factory):
    factory = platform_factory()
    assert factory.platform_name == "CFT"


def test_platform_factory_stores_platform_name_uppercased(platform_factory):
    factory = platform_factory(platform_name="etl")
    assert factory.platform_name == "ETL"


def test_platform_factory_accepts_cft(platform_factory):
    factory = platform_factory(platform_name="cft")
    assert factory.platform_name == "CFT"


def test_platform_factory_accepts_etl(platform_factory):
    factory = platform_factory(platform_name="etl")
    assert factory.platform_name == "ETL"


def test_platform_factory_accepts_internal(platform_factory):
    factory = platform_factory(platform_name="internal")
    assert factory.platform_name == "INTERNAL"


def test_platform_factory_already_uppercase_name(platform_factory):
    factory = platform_factory(platform_name="CFT")
    assert factory.platform_name == "CFT"


# ===========================================================================
# PlatformFactory.__call__
# ===========================================================================

def test_platform_factory_call_returns_cft_instance(mock_platforms, platform_factory, mock_cft):
    factory = platform_factory(platform_name="CFT")
    result = factory()
    mock_cft.assert_called_once()
    assert result == mock_cft.return_value


def test_platform_factory_call_returns_etl_instance(mock_platforms, platform_factory, mock_etl):
    factory = platform_factory(platform_name="ETL")
    result = factory()
    mock_etl.assert_called_once()
    assert result == mock_etl.return_value


def test_platform_factory_call_returns_internal_instance(mock_platforms, platform_factory, mock_internal):
    factory = platform_factory(platform_name="INTERNAL")
    result = factory()
    mock_internal.assert_called_once()
    assert result == mock_internal.return_value


def test_platform_factory_call_raises_key_error_for_unknown_platform(platform_factory):
    factory = platform_factory(platform_name="UNKNOWN")
    with pytest.raises(KeyError):
        factory()


# ===========================================================================
# get_application
# ===========================================================================

def test_get_application_returns_cft_instance(mock_platforms, mock_cft):
    from data_push_cft.output_platform import get_application
    result = get_application("CFT")
    mock_cft.assert_called_once()
    assert result == mock_cft.return_value


def test_get_application_returns_etl_instance(mock_platforms, mock_etl):
    from data_push_cft.output_platform import get_application
    result = get_application("ETL")
    mock_etl.assert_called_once()
    assert result == mock_etl.return_value


def test_get_application_returns_internal_instance(mock_platforms, mock_internal):
    from data_push_cft.output_platform import get_application
    result = get_application("INTERNAL")
    mock_internal.assert_called_once()
    assert result == mock_internal.return_value


def test_get_application_delegates_to_platform_factory(mock_platforms):
    from data_push_cft.output_platform import get_application, PlatformFactory
    with patch(
        "data_push_cft.output_platform.PlatformFactory", wraps=PlatformFactory
    ) as mock_factory:
        get_application("CFT")
        mock_factory.assert_called_once_with(platform_name="CFT")
