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
