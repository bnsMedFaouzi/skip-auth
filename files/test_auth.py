import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.file_manager_fixtures import (
    mock_src_cos_settings,
    mock_dest_cos_settings,
    mock_src_cos_settings_class,
    mock_dest_cos_settings_class,
    mock_service_instance,
    mock_service_class,
    mock_publication,
    file_manager,
)


# ===========================================================================
# __init__
# ===========================================================================

def test_init_sets_src_cos_from_settings(
    mock_src_cos_settings_class, mock_dest_cos_settings_class, mock_service_class
):
    from data_push_cft.output_platform.base.file_manager import BaseFileManager

    handler = BaseFileManager.__new__(BaseFileManager)

    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_service_class", return_value=mock_service_class):
        handler.__init__()

    assert handler._src_cos == mock_src_cos_settings_class.return_value.COS_NAME


def test_init_sets_dest_cos_from_settings(
    mock_src_cos_settings_class, mock_dest_cos_settings_class, mock_service_class
):
    from data_push_cft.output_platform.base.file_manager import BaseFileManager

    handler = BaseFileManager.__new__(BaseFileManager)

    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_service_class", return_value=mock_service_class):
        handler.__init__()

    assert handler._dest_cos == mock_dest_cos_settings_class.return_value.COS_NAME


def test_init_creates_service_with_cos_settings(
    mock_src_cos_settings_class, mock_dest_cos_settings_class, mock_service_class
):
    from data_push_cft.output_platform.base.file_manager import BaseFileManager

    handler = BaseFileManager.__new__(BaseFileManager)

    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_service_class", return_value=mock_service_class):
        handler.__init__()

    mock_service_class.assert_called_once_with(
        cos_settings=[
            mock_src_cos_settings_class.return_value,
            mock_dest_cos_settings_class.return_value,
        ]
    )


def test_init_sets_file_manager_instance(
    mock_src_cos_settings_class, mock_dest_cos_settings_class, mock_service_class
):
    from data_push_cft.output_platform.base.file_manager import BaseFileManager

    handler = BaseFileManager.__new__(BaseFileManager)

    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(handler, "_get_class_type", side_effect=fake_get_class_type), \
         patch.object(handler, "_get_service_class", return_value=mock_service_class):
        handler.__init__()

    assert handler._file_manager is mock_service_class.return_value


# ===========================================================================
# services property
# ===========================================================================

def test_services_property_returns_file_manager(file_manager, mock_service_instance):
    assert file_manager.services is mock_service_instance


# ===========================================================================
# upload_files — abstract stub
# ===========================================================================

def test_upload_files_is_callable(file_manager):
    assert callable(file_manager.upload_files)


def test_upload_files_calls_service(file_manager, mock_publication, mock_service_instance):
    file_manager.upload_files(publication=mock_publication)
    mock_service_instance.copy_publications_files.assert_called_once()


def test_upload_files_accepts_prefix_argument(file_manager, mock_publication):
    # Should not raise when prefix is provided
    file_manager.upload_files(publication=mock_publication, prefix="2024/01")


def test_upload_files_prefix_defaults_to_none(file_manager, mock_publication):
    # Should not raise when prefix is omitted
    file_manager.upload_files(publication=mock_publication)


# ===========================================================================
# __init_cos_settings__
# ===========================================================================

def test_init_cos_settings_returns_tuple_of_two(file_manager, mock_src_cos_settings_class, mock_dest_cos_settings_class):
    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(file_manager, "_get_class_type", side_effect=fake_get_class_type):
        result = file_manager.__init_cos_settings__()

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_init_cos_settings_returns_src_settings_instance(
    file_manager, mock_src_cos_settings_class, mock_dest_cos_settings_class
):
    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(file_manager, "_get_class_type", side_effect=fake_get_class_type):
        src, _ = file_manager.__init_cos_settings__()

    assert src is mock_src_cos_settings_class.return_value


def test_init_cos_settings_returns_dest_settings_instance(
    file_manager, mock_src_cos_settings_class, mock_dest_cos_settings_class
):
    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(file_manager, "_get_class_type", side_effect=fake_get_class_type):
        _, dest = file_manager.__init_cos_settings__()

    assert dest is mock_dest_cos_settings_class.return_value


def test_init_cos_settings_instantiates_src_class(
    file_manager, mock_src_cos_settings_class, mock_dest_cos_settings_class
):
    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(file_manager, "_get_class_type", side_effect=fake_get_class_type):
        file_manager.__init_cos_settings__()

    mock_src_cos_settings_class.assert_called_once()


def test_init_cos_settings_instantiates_dest_class(
    file_manager, mock_src_cos_settings_class, mock_dest_cos_settings_class
):
    def fake_get_class_type(attr_name):
        return {
            "SRC_COS_SETTINGS_CLASS": mock_src_cos_settings_class,
            "DEST_COS_SETTINGS_CLASS": mock_dest_cos_settings_class,
        }.get(attr_name)

    with patch.object(file_manager, "_get_class_type", side_effect=fake_get_class_type):
        file_manager.__init_cos_settings__()

    mock_dest_cos_settings_class.assert_called_once()


# ===========================================================================
# _get_service_class
# ===========================================================================

def test_get_service_class_delegates_to_get_class_type(file_manager):
    mock_cls = MagicMock()
    with patch.object(file_manager, "_get_class_type", return_value=mock_cls) as mock_get:
        result = file_manager._get_service_class()
    mock_get.assert_called_once_with("File_MANAGAER_SERVICES_CLASS")
    assert result is mock_cls


def test_get_service_class_returns_none_when_not_defined(file_manager):
    with patch.object(file_manager, "_get_class_type", return_value=None):
        result = file_manager._get_service_class()
    assert result is None
