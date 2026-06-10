import pytest
from unittest.mock import patch

from tests.fixtures.init_fixtures import (
    mock_argv_etl,
    mock_argv_cft,
    mock_argv_internal,
    mock_argv_default,
)


# ===========================================================================
# OutPutPlatformNames
# ===========================================================================

def test_output_platform_names_etl_value():
    from data_push_cft import OutPutPlatformNames
    assert OutPutPlatformNames.elt.value == "ETL"


def test_output_platform_names_cft_value():
    from data_push_cft import OutPutPlatformNames
    assert OutPutPlatformNames.cft.value == "CFT"


def test_output_platform_names_internal_value():
    from data_push_cft import OutPutPlatformNames
    assert OutPutPlatformNames.internal.value == "INTERNAL"


def test_output_platform_names_has_three_members():
    from data_push_cft import OutPutPlatformNames
    assert len(OutPutPlatformNames) == 3


def test_output_platform_names_default_is_etl():
    from data_push_cft import OutPutPlatformNames
    assert OutPutPlatformNames.elt.value == "ETL"


# ===========================================================================
# __PLATFORMS__
# ===========================================================================

def test_platforms_is_tuple():
    from data_push_cft import __PLATFORMS__
    assert isinstance(__PLATFORMS__, tuple)


def test_platforms_contains_etl():
    from data_push_cft import __PLATFORMS__
    assert "ETL" in __PLATFORMS__


def test_platforms_contains_cft():
    from data_push_cft import __PLATFORMS__
    assert "CFT" in __PLATFORMS__


def test_platforms_contains_internal():
    from data_push_cft import __PLATFORMS__
    assert "INTERNAL" in __PLATFORMS__


def test_platforms_length_matches_enum():
    from data_push_cft import OutPutPlatformNames, __PLATFORMS__
    assert len(__PLATFORMS__) == len(OutPutPlatformNames)


def test_platforms_values_match_enum_values():
    from data_push_cft import OutPutPlatformNames, __PLATFORMS__
    expected = tuple(elm.value for elm in OutPutPlatformNames)
    assert __PLATFORMS__ == expected


# ===========================================================================
# argparse — output_platform argument
# ===========================================================================

def test_parser_default_platform_is_etl(mock_argv_default):
    import importlib
    import data_push_cft
    importlib.reload(data_push_cft)
    assert data_push_cft.DATAPUSH_OUTPUT_PLATFORM == "ETL"


def test_parser_accepts_etl(mock_argv_etl):
    import importlib
    import data_push_cft
    importlib.reload(data_push_cft)
    assert data_push_cft.DATAPUSH_OUTPUT_PLATFORM == "ETL"


def test_parser_accepts_cft(mock_argv_cft):
    import importlib
    import data_push_cft
    importlib.reload(data_push_cft)
    assert data_push_cft.DATAPUSH_OUTPUT_PLATFORM == "CFT"


def test_parser_accepts_internal(mock_argv_internal):
    import importlib
    import data_push_cft
    importlib.reload(data_push_cft)
    assert data_push_cft.DATAPUSH_OUTPUT_PLATFORM == "INTERNAL"


def test_parser_output_platform_is_uppercased(mock_argv_etl):
    import importlib
    import data_push_cft
    importlib.reload(data_push_cft)
    assert data_push_cft.DATAPUSH_OUTPUT_PLATFORM == data_push_cft.DATAPUSH_OUTPUT_PLATFORM.upper()
