import pytest
from unittest.mock import MagicMock


# ===========================================================================
# TransferRequestPrams
# ===========================================================================

def test_transfer_request_prams_apitimeout_defaults_to_none():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams.model_construct()
    assert params.apitimeout is None


def test_transfer_request_prams_apitimeout_serialization_alias():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams.model_construct(apitimeout=30)
    assert "apitimeout" in params.model_dump(by_alias=True)


# ===========================================================================
# TransferRequestBody
# ===========================================================================

def test_transfer_request_body_requires_filename():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    with pytest.raises(Exception):
        TransferRequestBody()


def test_transfer_request_body_filename_serialized_as_fname():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    dumped = TransferRequestBody(filename="test.txt").model_dump(by_alias=True)
    assert dumped["fname"] == "test.txt"


def test_transfer_request_body_parm_defaults_to_none():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    assert TransferRequestBody(filename="test.txt").parm is None


def test_transfer_request_body_sync_defaults_to_yes():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    assert TransferRequestBody(filename="test.txt").sync == "YES"


# ===========================================================================
# CredsTransfer
# ===========================================================================

def test_creds_transfer_requires_username_and_password():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    with pytest.raises(Exception):
        CredsTransfer()


def test_creds_transfer_fields_assigned():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    creds = CredsTransfer(username="user", password="secret")
    assert creds.username == "user"
    assert creds.password == "secret"


# ===========================================================================
# TransferRequest
# ===========================================================================

def test_transfer_request_requires_all_fields():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    with pytest.raises(Exception):
        TransferRequest()


def test_transfer_request_fields_assigned():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    req = TransferRequest(idtu="IDTU123", ida="IDA456", idt="IDT789")
    assert req.idtu == "IDTU123"
    assert req.ida == "IDA456"
    assert req.idt == "IDT789"


# ===========================================================================
# CftFileInfo
# ===========================================================================

def test_cft_file_info_pivot_filename_returns_basename():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo.model_construct(name="/some/path/to/file.txt")
    assert file_info.pivot_filename == "file.txt"


def test_cft_file_info_pivot_filename_strips_directory():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo.model_construct(name="/dir/subdir/data.parquet")
    assert "/" not in file_info.pivot_filename
