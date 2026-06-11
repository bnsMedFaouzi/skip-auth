import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.internal_publisher_fixtures import (
    mock_settings,
    mock_file_info,
    publisher_client,
)


# ===========================================================================
# Class attributes
# ===========================================================================

def test_log_subject_value():
    from data_push_cft.output_platform.internal.clients.publisher import LOG_SUBJECT
    assert LOG_SUBJECT == "Call Publisher Service"


def test_get_taase_token_function_is_set():
    from data_push_cft.output_platform.internal.clients.publisher import ApiPublisherClient
    from data_push_cft.output_platform.internal import taase_token_manager
    assert ApiPublisherClient.GET_TAASE_TOKEN_FUNCTION is taase_token_manager.get_token


# ===========================================================================
# transfer_file
# ===========================================================================

def test_transfer_file_calls_request_with_token_post(publisher_client, mock_file_info):
    publisher_client.transfer_file(mock_file_info)
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["method"] == "post"


def test_transfer_file_uses_get_push_uri_template(publisher_client, mock_file_info, mock_settings):
    publisher_client.transfer_file(mock_file_info)
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.get_push_uri_template


def test_transfer_file_passes_serialized_body(publisher_client, mock_file_info):
    publisher_client.transfer_file(mock_file_info)
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["data"] == mock_file_info.model_dump_json.return_value


def test_transfer_file_returns_none(publisher_client, mock_file_info):
    result = publisher_client.transfer_file(mock_file_info)
    assert result is None


# ===========================================================================
# health_check
# ===========================================================================

def test_health_check_calls_request_with_token_get(publisher_client):
    publisher_client.health_check()
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["method"] == "get"


def test_health_check_uses_health_check_uri(publisher_client, mock_settings):
    publisher_client.health_check()
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.health_check_uri


def test_health_check_returns_response(publisher_client):
    mock_response = MagicMock()
    publisher_client.request_with_token.return_value = mock_response
    result = publisher_client.health_check()
    assert result is mock_response
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
