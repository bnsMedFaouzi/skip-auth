import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.file_transfer_fixtures import (
    file_transfer_client,
    concrete_file_transfer_client,
)


# ===========================================================================
# FileTransferClient — transfer_file
# ===========================================================================

def test_transfer_file_raises_not_implemented_error(file_transfer_client):
    with pytest.raises(NotImplementedError):
        file_transfer_client.transfer_file()


def test_transfer_file_raises_not_implemented_error_with_args(file_transfer_client):
    with pytest.raises(NotImplementedError):
        file_transfer_client.transfer_file("arg1", "arg2")


def test_transfer_file_raises_not_implemented_error_with_kwargs(file_transfer_client):
    with pytest.raises(NotImplementedError):
        file_transfer_client.transfer_file(filename="test.json", bucket="my-bucket")


def test_transfer_file_error_message(file_transfer_client):
    with pytest.raises(NotImplementedError, match="Method not implemented"):
        file_transfer_client.transfer_file()


# ===========================================================================
# FileTransferClient — health_check
# ===========================================================================

def test_health_check_raises_not_implemented_error(file_transfer_client):
    with pytest.raises(NotImplementedError):
        file_transfer_client.health_check()


def test_health_check_error_message(file_transfer_client):
    with pytest.raises(NotImplementedError, match="Method not implemented"):
        file_transfer_client.health_check()


# ===========================================================================
# FileTransferClient — inheritance & contract
# ===========================================================================

def test_file_transfer_client_inherits_from_http_client(file_transfer_client):
    from data_push_cft.client.file_transfer import FileTransferClient
    from bnppam_mercury.core.client import HttpClient
    assert issubclass(FileTransferClient, HttpClient)


def test_file_transfer_client_has_transfer_file_method(file_transfer_client):
    assert hasattr(file_transfer_client, "transfer_file")
    assert callable(file_transfer_client.transfer_file)


def test_file_transfer_client_has_health_check_method(file_transfer_client):
    assert hasattr(file_transfer_client, "health_check")
    assert callable(file_transfer_client.health_check)


# ===========================================================================
# ConcreteClient — subclass can override without errors
# ===========================================================================

def test_concrete_subclass_transfer_file_does_not_raise(concrete_file_transfer_client):
    result = concrete_file_transfer_client.transfer_file()
    assert result is not None


def test_concrete_subclass_health_check_does_not_raise(concrete_file_transfer_client):
    result = concrete_file_transfer_client.health_check()
    assert result is not None


def test_concrete_subclass_transfer_file_accepts_args(concrete_file_transfer_client):
    result = concrete_file_transfer_client.transfer_file("arg1", key="value")
    assert result is not None
