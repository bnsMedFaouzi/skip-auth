import pytest
from unittest.mock import MagicMock, patch, call
from fastapi import HTTPException
from pydantic import BaseModel

from tests.fixtures.interface_fixtures import (
    mock_client,
    mock_client_settings_class,
    mock_client_class,
    mock_file_info,
    mock_files_info,
    http_exception_rejected,
    http_exception_retryable,
    http_exception_unknown,
    interface,
)


# ===========================================================================
# __init__ — client initialization
# ===========================================================================

def test_init_creates_client_with_settings(mock_client_settings_class, mock_client_class):
    from data_push_cft.output_platform.base.interface import BasePlatformInterface

    handler = BasePlatformInterface.__new__(BasePlatformInterface)

    def fake_get_class_type(attr_name):
        return {
            "PLATFORM_CLIENT_SETTINGS_CLASS": mock_client_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_client_class", return_value=mock_client_class):
        handler.__init__()

    mock_client_settings_class.assert_called_once()
    mock_client_class.assert_called_once_with(settings=mock_client_settings_class.return_value)


def test_init_sets_client_instance(mock_client_settings_class, mock_client_class):
    from data_push_cft.output_platform.base.interface import BasePlatformInterface

    handler = BasePlatformInterface.__new__(BasePlatformInterface)

    def fake_get_class_type(attr_name):
        return {
            "PLATFORM_CLIENT_SETTINGS_CLASS": mock_client_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_client_class", return_value=mock_client_class):
        handler.__init__()

    assert handler._client is mock_client_class.return_value


# ===========================================================================
# client property
# ===========================================================================

def test_client_property_returns_client(interface, mock_client):
    assert interface.client is mock_client


# ===========================================================================
# push_files
# ===========================================================================

def test_push_files_returns_list(interface, mock_files_info):
    with patch.object(interface, "_push_file", return_value=MagicMock(spec=BaseModel)):
        result = interface.push_files(mock_files_info)
    assert isinstance(result, list)


def test_push_files_returns_one_result_per_file(interface, mock_files_info):
    with patch.object(interface, "_push_file", return_value=MagicMock(spec=BaseModel)):
        result = interface.push_files(mock_files_info)
    assert len(result) == len(mock_files_info)


def test_push_files_calls_push_file_for_each_file(interface, mock_files_info):
    with patch.object(interface, "_push_file", return_value=MagicMock()) as mock_push:
        interface.push_files(mock_files_info)
    assert mock_push.call_count == len(mock_files_info)


def test_push_files_passes_kwargs_to_push_file(interface, mock_files_info):
    with patch.object(interface, "_push_file", return_value=MagicMock()) as mock_push:
        interface.push_files(mock_files_info, bucket="my-bucket", prefix="data/")
    for c in mock_push.call_args_list:
        assert c.kwargs.get("bucket") == "my-bucket"
        assert c.kwargs.get("prefix") == "data/"


def test_push_files_calls_resolve_action_on_http_exception(
    interface, mock_files_info, http_exception_rejected
):
    with patch.object(interface, "_push_file", side_effect=http_exception_rejected), \
         patch.object(interface, "_resolve_action") as mock_resolve:
        interface.push_files(mock_files_info)
    mock_resolve.assert_called_once_with(http_exception_rejected)


def test_push_files_with_empty_list_returns_empty_list(interface):
    result = interface.push_files([])
    assert result == []


# ===========================================================================
# check_liveness
# ===========================================================================

def test_check_liveness_calls_health_check(interface, mock_client):
    interface.check_liveness()
    mock_client.health_check.assert_called_once()


def test_check_liveness_calls_resolve_action_on_http_exception(
    interface, mock_client, http_exception_retryable
):
    mock_client.health_check.side_effect = http_exception_retryable
    with patch.object(interface, "_resolve_action") as mock_resolve:
        interface.check_liveness()
    mock_resolve.assert_called_once_with(http_exception_retryable)


# ===========================================================================
# _resolve_action
# ===========================================================================

def test_resolve_action_raises_rejected_exception_for_4xx(
    interface, http_exception_rejected
):
    from data_push_cft.output_platform.exceptiones import RejectedException
    with pytest.raises(RejectedException):
        interface._resolve_action(http_exception_rejected)


def test_resolve_action_raises_retryable_exception_for_5xx(
    interface, http_exception_retryable
):
    from data_push_cft.output_platform.exceptiones import RetryableException
    with pytest.raises(RetryableException):
        interface._resolve_action(http_exception_retryable)


def test_resolve_action_does_not_raise_for_unknown_status(
    interface, http_exception_unknown
):
    # 3xx — neither rejected nor retryable → no exception
    interface._resolve_action(http_exception_unknown)


def test_resolve_action_rejected_status_boundary_400(interface):
    from data_push_cft.output_platform.exceptiones import RejectedException
    e = HTTPException(status_code=400)
    with pytest.raises(RejectedException):
        interface._resolve_action(e)


def test_resolve_action_rejected_status_boundary_499(interface):
    from data_push_cft.output_platform.exceptiones import RejectedException
    e = HTTPException(status_code=499)
    with pytest.raises(RejectedException):
        interface._resolve_action(e)


def test_resolve_action_retryable_status_boundary_500(interface):
    from data_push_cft.output_platform.exceptiones import RetryableException
    e = HTTPException(status_code=500)
    with pytest.raises(RetryableException):
        interface._resolve_action(e)


def test_resolve_action_retryable_status_boundary_599(interface):
    from data_push_cft.output_platform.exceptiones import RetryableException
    e = HTTPException(status_code=599)
    with pytest.raises(RetryableException):
        interface._resolve_action(e)


# ===========================================================================
# _get_client_class
# ===========================================================================

def test_get_client_class_delegates_to_get_class_type(interface):
    mock_class = MagicMock()
    with patch.object(interface, "_get_class_type", return_value=mock_class) as mock_get:
        result = interface._get_client_class()
    mock_get.assert_called_once_with("PLATFORM_CLIENT_CLASS")
    assert result is mock_class


# ===========================================================================
# _push_file
# ===========================================================================

def test_push_file_calls_client_transfer_file(interface, mock_client, mock_file_info):
    interface._push_file(mock_file_info)
    mock_client.transfer_file.assert_called_once()


def test_push_file_passes_file_info_to_transfer_file(interface, mock_client, mock_file_info):
    interface._push_file(mock_file_info)
    call_args = mock_client.transfer_file.call_args
    assert mock_file_info in call_args.args or mock_file_info in call_args.kwargs.values()


def test_push_file_passes_kwargs_to_transfer_file(interface, mock_client, mock_file_info):
    interface._push_file(mock_file_info, bucket="test-bucket")
    call_kwargs = mock_client.transfer_file.call_args.kwargs
    assert call_kwargs.get("bucket") == "test-bucket"


def test_push_file_returns_result_from_transfer_file(interface, mock_client, mock_file_info):
    mock_result = MagicMock(spec=BaseModel)
    mock_client.transfer_file.return_value = mock_result
    result = interface._push_file(mock_file_info)
    assert result is mock_result
