import pytest
from unittest.mock import patch

from data_push_cft.output_platform.base.mixin import BaseApplicationMixin
from data_push_cft.output_platform.base.event_handler import BaseEventHandler
from data_push_cft.output_platform.base.file_manager import BaseFileManager
from data_push_cft.output_platform.base.interface import BasePlatformInterface


# ===========================================================================
# __PLATFORM_NAME__
# ===========================================================================

def test_platform_name_value_is_base_platform():
    assert BaseApplicationMixin.__PLATFORM_NAME__ == "BASE_PLATFORM"


def test_platform_name_is_string():
    assert isinstance(BaseApplicationMixin.__PLATFORM_NAME__, str)


def test_platform_name_is_uppercase():
    assert BaseApplicationMixin.__PLATFORM_NAME__ == BaseApplicationMixin.__PLATFORM_NAME__.upper()


# ===========================================================================
# Inheritance
# ===========================================================================

def test_inherits_from_base_file_manager():
    assert issubclass(BaseApplicationMixin, BaseFileManager)


def test_inherits_from_base_platform_interface():
    assert issubclass(BaseApplicationMixin, BasePlatformInterface)


def test_inherits_from_base_event_handler():
    assert issubclass(BaseApplicationMixin, BaseEventHandler)


# ===========================================================================
# MRO — resolution order
# ===========================================================================

def test_mro_file_manager_before_platform_interface():
    mro = BaseApplicationMixin.__mro__
    assert mro.index(BaseFileManager) < mro.index(BasePlatformInterface)


def test_mro_platform_interface_before_event_handler():
    mro = BaseApplicationMixin.__mro__
    assert mro.index(BasePlatformInterface) < mro.index(BaseEventHandler)


def test_mro_contains_all_three_bases():
    mro = BaseApplicationMixin.__mro__
    assert BaseFileManager in mro
    assert BasePlatformInterface in mro
    assert BaseEventHandler in mro


# ===========================================================================
# Inherited methods presence
# ===========================================================================

def test_has_upload_files_from_file_manager():
    assert hasattr(BaseApplicationMixin, "upload_files")


def test_has_push_files_from_platform_interface():
    assert hasattr(BaseApplicationMixin, "push_files")


def test_has_notify_from_event_handler():
    assert hasattr(BaseApplicationMixin, "notify")


def test_has_check_liveness_from_platform_interface():
    assert hasattr(BaseApplicationMixin, "check_liveness")


def test_has_services_property_from_file_manager():
    assert hasattr(BaseApplicationMixin, "services")


def test_has_consumer_property_from_event_handler():
    assert hasattr(BaseApplicationMixin, "consumer")


def test_has_client_property_from_platform_interface():
    assert hasattr(BaseApplicationMixin, "client")
