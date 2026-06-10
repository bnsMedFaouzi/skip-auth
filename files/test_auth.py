import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.cft_client_fixtures import (
    mock_settings,
    mock_hv_services,
    mock_file_info,
    cft_client,
)


# ===========================================================================
# transfer_file
# Fix: patch TransferRequestPrams.model_validate to bypass CftFlow validation
# ===========================================================================

def test_transfer_file_calls_request_with_post(cft_client, mock_file_info):
    mock_response = MagicMock()
    mock_response.json.return_value = {"idtu": "T1", "ida": "A1", "idt": "D1"}
    cft_client.request_with_basic_auth = MagicMock(return_value=mock_response)

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})), \
         patch("data_push_cft.output_platform.cft.client.TransferRequestPrams") as mock_prams:
        mock_prams.model_validate.return_value.model_dump.return_value = {}
        cft_client.transfer_file(mock_file_info)

    call_kwargs = cft_client.request_with_basic_auth.call_args.kwargs
    assert call_kwargs["method"] == "post"


def test_transfer_file_uses_transfer_uri(cft_client, mock_file_info, mock_settings):
    mock_response = MagicMock()
    mock_response.json.return_value = {"idtu": "T1", "ida": "A1", "idt": "D1"}
    cft_client.request_with_basic_auth = MagicMock(return_value=mock_response)

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})), \
         patch("data_push_cft.output_platform.cft.client.TransferRequestPrams") as mock_prams:
        mock_prams.model_validate.return_value.model_dump.return_value = {}
        cft_client.transfer_file(mock_file_info)

    call_kwargs = cft_client.request_with_basic_auth.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.transfer_file_uri_template


def test_transfer_file_returns_transfer_request(cft_client, mock_file_info):
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    mock_response = MagicMock()
    mock_response.json.return_value = {"idtu": "T1", "ida": "A1", "idt": "D1"}
    cft_client.request_with_basic_auth = MagicMock(return_value=mock_response)

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})), \
         patch("data_push_cft.output_platform.cft.client.TransferRequestPrams") as mock_prams:
        mock_prams.model_validate.return_value.model_dump.return_value = {}
        result = cft_client.transfer_file(mock_file_info)

    assert isinstance(result, TransferRequest)


# ===========================================================================
# health_check
# ===========================================================================

def test_health_check_calls_request_with_get(cft_client, mock_settings):
    mock_response = MagicMock()
    cft_client.request_with_basic_auth = MagicMock(return_value=mock_response)

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})):
        cft_client.health_check()

    call_kwargs = cft_client.request_with_basic_auth.call_args.kwargs
    assert call_kwargs["method"] == "get"


def test_health_check_uses_health_check_uri(cft_client, mock_settings):
    cft_client.request_with_basic_auth = MagicMock(return_value=MagicMock())

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})):
        cft_client.health_check()

    call_kwargs = cft_client.request_with_basic_auth.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.health_check_uri


def test_health_check_returns_response(cft_client):
    mock_response = MagicMock()
    cft_client.request_with_basic_auth = MagicMock(return_value=mock_response)

    with patch.object(cft_client, "_get_creds", return_value=MagicMock(model_dump=lambda: {})):
        result = cft_client.health_check()

    assert result is mock_response


# ===========================================================================
# _get_creds
# ===========================================================================

def test_get_creds_calls_hv_services_get_secret(cft_client, mock_hv_services, mock_settings):
    cft_client._get_creds()
    mock_hv_services.get_secret.assert_called_once_with(
        path=mock_settings.CFT_SECRET_PATH,
        mount_point=mock_settings.CFT_HVAULT_MOUNTPOINT,
        is_dynamic=False,
        subsystem="CFT"
    )


def test_get_creds_returns_creds_transfer(cft_client):
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    result = cft_client._get_creds()
    assert isinstance(result, CredsTransfer)


def test_get_creds_uses_settings_username(cft_client, mock_settings):
    result = cft_client._get_creds()
    assert result.username == mock_settings.CFT_UESRNAME


# ===========================================================================
# _request (staticmethod)
# ===========================================================================

def test_request_calls_correct_session_method():
    from data_push_cft.output_platform.cft.client import CftClient
    mock_session = MagicMock()
    CftClient._request(session=mock_session, method="get", url="https://example.com")
    mock_session.get.assert_called_once()


def test_request_passes_url_and_params():
    from data_push_cft.output_platform.cft.client import CftClient
    mock_session = MagicMock()
    CftClient._request(
        session=mock_session,
        method="post",
        url="https://example.com",
        params={"key": "val"},
        data={"body": "data"}
    )
    call_kwargs = mock_session.post.call_args.kwargs
    assert call_kwargs["url"] == "https://example.com"
    assert call_kwargs["params"] == {"key": "val"}
    assert call_kwargs["verify"] is False


def test_request_returns_response():
    from data_push_cft.output_platform.cft.client import CftClient
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_session.get.return_value = mock_response
    result = CftClient._request(session=mock_session, method="get", url="https://example.com")
    assert result is mock_response
