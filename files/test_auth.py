import pytest
from typing import Optional
from unittest.mock import MagicMock, patch


# ===========================================================================
# TransferRequestPrams
# ===========================================================================

def test_transfer_request_prams_apitimeout_defaults_to_none():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams()
    assert params.apitimeout is None


def test_transfer_request_prams_apitimeout_accepts_int():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams(apitimeout=30)
    assert params.apitimeout == 30


def test_transfer_request_prams_apitimeout_serialization_alias():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams(apitimeout=30)
    dumped = params.model_dump(by_alias=True)
    assert "apitimeout" in dumped


def test_transfer_request_prams_apitimeout_serialized_value():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams(apitimeout=30)
    dumped = params.model_dump(by_alias=True)
    assert dumped["apitimeout"] == 30


def test_transfer_request_prams_apitimeout_none_in_dump():
    from data_push_cft.output_platform.cft.schemas import TransferRequestPrams
    params = TransferRequestPrams()
    dumped = params.model_dump(by_alias=True)
    assert dumped["apitimeout"] is None


# ===========================================================================
# TransferRequestBody
# ===========================================================================

def test_transfer_request_body_requires_filename():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    with pytest.raises(Exception):
        TransferRequestBody()


def test_transfer_request_body_filename_assigned():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt")
    assert body.filename == "test.txt"


def test_transfer_request_body_filename_serialization_alias():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt")
    dumped = body.model_dump(by_alias=True)
    assert "fname" in dumped
    assert dumped["fname"] == "test.txt"


def test_transfer_request_body_parm_defaults_to_none():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt")
    assert body.parm is None


def test_transfer_request_body_parm_accepts_value():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt", parm="my-param")
    assert body.parm == "my-param"


def test_transfer_request_body_parm_serialization_alias():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt", parm="val")
    dumped = body.model_dump(by_alias=True)
    assert "parm" in dumped
    assert dumped["parm"] == "val"


def test_transfer_request_body_sync_defaults_to_yes():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt")
    assert body.sync == "YES"


def test_transfer_request_body_sync_can_be_overridden():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt", sync="NO")
    assert body.sync == "NO"


def test_transfer_request_body_sync_serialization_alias():
    from data_push_cft.output_platform.cft.schemas import TransferRequestBody
    body = TransferRequestBody(filename="test.txt")
    dumped = body.model_dump(by_alias=True)
    assert "sync" in dumped
    assert dumped["sync"] == "YES"


# ===========================================================================
# CredsTransfer
# ===========================================================================

def test_creds_transfer_requires_username_and_password():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    with pytest.raises(Exception):
        CredsTransfer()


def test_creds_transfer_username_assigned():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    creds = CredsTransfer(username="user", password="secret")
    assert creds.username == "user"


def test_creds_transfer_password_assigned():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    creds = CredsTransfer(username="user", password="secret")
    assert creds.password == "secret"


def test_creds_transfer_username_is_str():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    creds = CredsTransfer(username="user", password="secret")
    assert isinstance(creds.username, str)


def test_creds_transfer_password_is_str():
    from data_push_cft.output_platform.cft.schemas import CredsTransfer
    creds = CredsTransfer(username="user", password="secret")
    assert isinstance(creds.password, str)


# ===========================================================================
# TransferRequest
# ===========================================================================

def test_transfer_request_requires_all_fields():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    with pytest.raises(Exception):
        TransferRequest()


def test_transfer_request_idtu_assigned():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    req = TransferRequest(idtu="IDTU123", ida="IDA456", idt="IDT789")
    assert req.idtu == "IDTU123"


def test_transfer_request_ida_assigned():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    req = TransferRequest(idtu="IDTU123", ida="IDA456", idt="IDT789")
    assert req.ida == "IDA456"


def test_transfer_request_idt_assigned():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    req = TransferRequest(idtu="IDTU123", ida="IDA456", idt="IDT789")
    assert req.idt == "IDT789"


def test_transfer_request_all_fields_are_str():
    from data_push_cft.output_platform.cft.schemas import TransferRequest
    req = TransferRequest(idtu="IDTU123", ida="IDA456", idt="IDT789")
    assert isinstance(req.idtu, str)
    assert isinstance(req.ida, str)
    assert isinstance(req.idt, str)


# ===========================================================================
# CftFileInfo — pivot_filename property
# ===========================================================================

def test_cft_file_info_pivot_filename_returns_basename():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo(name="/some/path/to/file.txt", cft_flow=MagicMock())
    assert file_info.pivot_filename == "file.txt"


def test_cft_file_info_pivot_filename_with_simple_name():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo(name="myfile.csv", cft_flow=MagicMock())
    assert file_info.pivot_filename == "myfile.csv"


def test_cft_file_info_pivot_filename_with_nested_path():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo(name="/a/b/c/d/report.json", cft_flow=MagicMock())
    assert file_info.pivot_filename == "report.json"


def test_cft_file_info_pivot_filename_strips_directory():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    file_info = CftFileInfo(name="/dir/subdir/data.parquet", cft_flow=MagicMock())
    assert "/" not in file_info.pivot_filename


def test_cft_file_info_cft_flow_assigned():
    from data_push_cft.output_platform.cft.schemas import CftFileInfo
    mock_flow = MagicMock()
    file_info = CftFileInfo(name="file.txt", cft_flow=mock_flow)
    assert file_info.cft_flow is mock_flow
