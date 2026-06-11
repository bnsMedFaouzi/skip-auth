import pytest
from unittest.mock import patch

from tests.fixtures.internal_settings_fixtures import (
    internal_kafka_env,
    internal_publisher_settings_env,
)


# ===========================================================================
# KafkaConsumerSettings
# ===========================================================================

def test_internal_kafka_topic_name_loaded_from_env(internal_kafka_env):
    from data_push_cft.output_platform.internal.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    assert settings.TOPIC_NAME == "internal-topic"


def test_internal_kafka_group_name_loaded_from_env(internal_kafka_env):
    from data_push_cft.output_platform.internal.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    assert settings.GROUP_NAME == "internal-group"


def test_internal_kafka_group_name_serialization_alias(internal_kafka_env):
    from data_push_cft.output_platform.internal.settings import KafkaConsumerSettings
    settings = KafkaConsumerSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "group.id" in dumped
    assert dumped["group.id"] == "internal-group"


# ===========================================================================
# ApiPublisherSettings — default values
# ===========================================================================

def test_api_publisher_default_get_metadata_uri(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.GET_METADATA_URI == "/v1/publisher_service/publication/push"


def test_api_publisher_default_health_check_uri_field(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.HEALTH_CHECK_URI == "/v1/publisher_service/health_check"


def test_api_publisher_get_metadata_uri_can_be_overridden(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    with patch.dict("os.environ", {"API_PUBLISHER_PUSH_URI": "/custom/push"}):
        settings = ApiPublisherSettings()
    assert settings.GET_METADATA_URI == "/custom/push"


# ===========================================================================
# ApiPublisherSettings — computed properties
# ===========================================================================

def test_get_push_uri_template_concatenates_base_url_and_uri(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.get_push_uri_template == f"{settings.BASE_URL}{settings.GET_METADATA_URI}"


def test_get_push_uri_template_starts_with_base_url(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.get_push_uri_template.startswith("https://publisher.example.com")


def test_health_check_uri_concatenates_base_url_and_uri(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.health_check_uri == f"{settings.BASE_URL}{settings.HEALTH_CHECK_URI}"


def test_health_check_uri_starts_with_base_url(internal_publisher_settings_env):
    from data_push_cft.output_platform.internal.settings import ApiPublisherSettings
    settings = ApiPublisherSettings()
    assert settings.health_check_uri.startswith("https://publisher.example.com")
    publisher_client.transfer_file(mock_file_info)
    call_kwargs = publisher_client.request_with_token.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.get_push_uri_template
