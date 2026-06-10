import pytest
from unittest.mock import patch

from tests.fixtures.cft_settings_fixtures import (
    cft_settings_env,
    cft_kafka_consumer_env,
    cft_public_cos_env,
)


# ===========================================================================
# CftSettings — field loading
# ===========================================================================

def test_cft_settings_base_url_loaded_from_env(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.BASE_URL == "https://cft.example.com"


def test_cft_settings_hvault_mountpoint_loaded_from_env(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.CFT_HVAULT_MOUNTPOINT == "/vault/mount"


def test_cft_settings_secret_path_loaded_from_env(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.CFT_SECRET_PATH == "/secret/path"


def test_cft_settings_username_loaded_from_env(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.CFT_UESRNAME == "cft-user"


# ===========================================================================
# CftSettings — default values
# ===========================================================================

def test_cft_settings_default_transfer_file_uri(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.TRANSFER_FILE_URI == "/cft/api/v1/transfers/files/outgoings"


def test_cft_settings_default_health_check_uri(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.HEALTH_CHECK_URI == "/cft/api/v1/about"


def test_cft_settings_default_password_key(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.CFT_PASSWORD_KEY == "password"


def test_cft_settings_transfer_file_uri_can_be_overridden(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    with patch.dict("os.environ", {"CFT_TRANSFER_FILE_URI": "/custom/uri"}):
        settings = CftSettings()
    assert settings.TRANSFER_FILE_URI == "/custom/uri"


# ===========================================================================
# CftSettings — computed properties
# ===========================================================================

def test_transfer_file_uri_template_concatenates_base_url_and_uri(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    expected = f"{settings.BASE_URL}{settings.TRANSFER_FILE_URI}"
    assert settings.transfer_file_uri_template == expected


def test_transfer_file_uri_template_starts_with_base_url(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.transfer_file_uri_template.startswith("https://cft.example.com")


def test_transfer_file_uri_template_contains_transfer_path(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert "/cft/api/v1/transfers/files/outgoings" in settings.transfer_file_uri_template


def test_health_check_uri_concatenates_base_url_and_uri(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    expected = f"{settings.BASE_URL}{settings.HEALTH_CHECK_URI}"
    assert settings.health_check_uri == expected


def test_health_check_uri_starts_with_base_url(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert settings.health_check_uri.startswith("https://cft.example.com")


def test_health_check_uri_contains_about_path(cft_settings_env):
    from data_push_cft.output_platform.cft.settings import CftSettings
    settings = CftSettings()
    assert "/cft/api/v1/about" in settings.health_check_uri


# ===========================================================================
# KafkaConsumerSettings
# ===========================================================================

def test_cft_kafka_topic_name_loaded_from_env(cft_kafka_consumer_env):
    from data_push_cft.output_platform.cft.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    assert settings.TOPIC_NAME == "cft-topic"


def test_cft_kafka_group_name_loaded_from_env(cft_kafka_consumer_env):
    from data_push_cft.output_platform.cft.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    assert settings.GROUP_NAME == "cft-group"


def test_cft_kafka_group_name_serialization_alias(cft_kafka_consumer_env):
    from data_push_cft.output_platform.cft.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "group.id" in dumped


def test_cft_kafka_group_name_serialized_value(cft_kafka_consumer_env):
    from data_push_cft.output_platform.cft.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    dumped = settings.model_dump(by_alias=True)
    assert dumped["group.id"] == "cft-group"


# ===========================================================================
# PublicCosSettings
# ===========================================================================

def test_cft_public_cos_bucket_name_loaded_from_env(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    assert settings.BUCKET_NAME == "cft-bucket"


def test_cft_public_cos_bucket_endpoint_loaded_from_env(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    assert settings.BUCKET_ENDPOINT == "https://cft-cos.example.com"


def test_cft_public_cos_name_loaded_from_env(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    assert settings.COS_NAME == "cft-cos"


def test_cft_public_cos_bucket_excluded_from_dump(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "PUBLIC_DATA_PUSH_CFT_BUCKET" not in dumped


def test_cft_public_cos_endpoint_excluded_from_dump(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "PUBLIC_DATA_PUSH_CFT_BUCKET_ENDPOINT" not in dumped


def test_cft_public_cos_name_excluded_from_dump(cft_public_cos_env):
    from data_push_cft.output_platform.cft.settings import PublicCosSettings
    settings = PublicCosSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "PUBLIC_DATA_PUSH_CFT_COS_NAME" not in dumped
