import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from tests.fixtures.cft_application_fixtures import (
    cft_app,
    mock_file_info,
    mock_cft_flow,
)


# ===========================================================================
# Class attributes
# ===========================================================================

def test_platform_name_is_cft():
    from data_push_cft.output_platform.cft.application import Cft
    assert Cft.__PLATFORM_NAME__ == "CFT"


def test_message_filter_headers():
    from data_push_cft.output_platform.cft.application import Cft
    assert Cft.MESSAGE_FILTER_HEADERS == {"CFT": "1"}


def test_notify_is_false():
    from data_push_cft.output_platform.cft.application import Cft
    assert Cft.NOTIFY is False


def test_platform_client_class_is_cft_client():
    from data_push_cft.output_platform.cft.application import Cft
    from data_push_cft.output_platform.cft.client import CftClient
    assert Cft.PLATFORM_CLIENT_CLASS is CftClient


def test_platform_client_settings_class_is_cft_settings():
    from data_push_cft.output_platform.cft.application import Cft
    from data_push_cft.output_platform.cft.settings import CftSettings
    assert Cft.PLATFORM_CLIENT_SETTINGS_CLASS is CftSettings


# ===========================================================================
# _push_file
# ===========================================================================

def test_push_file_strips_leading_path_segment(cft_app, mock_file_info):
    mock_file_info.path = "bucket/subdir/file.txt"
    with patch.object(type(cft_app).__mro__[1], "_push_file", return_value=MagicMock()):
        cft_app._push_file(mock_file_info)
    assert mock_file_info.path == "subdir/file.txt"


def test_push_file_calls_super_push_file(cft_app, mock_file_info):
    with patch(
        "data_push_cft.output_platform.cft.application.super"
    ) as mock_super:
        mock_super.return_value._push_file = MagicMock(return_value=MagicMock())
        cft_app._push_file(mock_file_info)
    mock_super.return_value._push_file.assert_called_once_with(mock_file_info)


# ===========================================================================
# serialise_cft_upload_files
# ===========================================================================

def test_serialise_cft_upload_files_returns_list(mock_cft_flow):
    from data_push_cft.output_platform.cft.application import Cft
    transferred_files = [MagicMock(), MagicMock()]
    for f in transferred_files:
        f.model_dump.return_value = {"name": "file.txt"}

    with patch("data_push_cft.output_platform.cft.application.CftFileInfo") as mock_cft_file_info:
        mock_cft_file_info.model_validate.return_value = MagicMock()
        result = Cft.serialise_cft_upload_files(transferred_files, mock_cft_flow)

    assert isinstance(result, list)
    assert len(result) == 2


def test_serialise_cft_upload_files_adds_cft_flow(mock_cft_flow):
    from data_push_cft.output_platform.cft.application import Cft
    mock_file = MagicMock()
    mock_file.model_dump.return_value = {"name": "file.txt"}

    captured_calls = []
    with patch("data_push_cft.output_platform.cft.application.CftFileInfo") as mock_cft_file_info:
        def capture(data):
            captured_calls.append(data)
            return MagicMock()
        mock_cft_file_info.model_validate.side_effect = capture
        Cft.serialise_cft_upload_files([mock_file], mock_cft_flow)

    assert captured_calls[0].get("cft_flow") is mock_cft_flow


def test_serialise_cft_upload_files_empty_list(mock_cft_flow):
    from data_push_cft.output_platform.cft.application import Cft
    result = Cft.serialise_cft_upload_files([], mock_cft_flow)
    assert result == []


# ===========================================================================
# _resolve_action
# ===========================================================================

def test_resolve_action_always_raises_retryable_exception(cft_app):
    from data_push_cft.output_platform.exceptiones import RetryableException
    e = HTTPException(status_code=400)
    with pytest.raises(RetryableException):
        cft_app._resolve_action(e)


def test_resolve_action_raises_for_any_status_code(cft_app):
    from data_push_cft.output_platform.exceptiones import RetryableException
    for status_code in [400, 404, 500, 503]:
        e = HTTPException(status_code=status_code)
        with pytest.raises(RetryableException):
            cft_app._resolve_action(e)
