import os
import pytest
from unittest.mock import patch

from output_platform.settings import (
    KafkaProducerSettings,
    PrivateCosSettings,
    PublicCosSettings,
    DataPushSettings,
)
from tests.fixtures.settings_fixtures import (
    kafka_settings_env,
    private_cos_settings_env,
    public_cos_settings_env,
    data_push_settings_env,
    data_push_settings_dev_env,
    data_push_settings_prod_env,
    data_push_settings_local_env,
    data_push_settings_not_local_env,
)


# ===========================================================================
# KafkaProducerSettings
# ===========================================================================

def test_kafka_topic_name_loaded_from_env(kafka_settings_env):
    settings = KafkaProducerSettings()
    assert settings.TOPIC_NAME == "test-topic"


def test_kafka_group_name_loaded_from_env(kafka_settings_env):
    settings = KafkaProducerSettings()
    assert settings.GROUP_NAME == "test-group"


def test_kafka_topic_name_alias_is_kafka_topic_public(kafka_settings_env):
    settings = KafkaProducerSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "KAFKA_TOPIC_PUBLIC" in dumped


def test_kafka_group_name_alias_is_kafka_group(kafka_settings_env):
    settings = KafkaProducerSettings()
    dumped = settings.model_dump(by_alias=True)
    assert "KAFKA_TOPIC_PUBLIC_DATA_PUSH_GROUP" in dumped


# ===========================================================================
# BaseCosSettings (tested via PrivateCosSettings — concrete subclass)
# ===========================================================================

def test_base_cos_templates_path_is_absolute(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert os.path.isabs(settings.templates_path)


def test_base_cos_templates_path_ends_with_templates(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert settings.templates_path.endswith("templates")


def test_base_cos_default_location_path_template_returns_filename(private_cos_settings_env):
    settings = PrivateCosSettings()
    result = settings.default_location_path_template("myfile.json")
    assert result == "myfile.json"


def test_base_cos_default_location_path_template_ignores_kwargs(private_cos_settings_env):
    settings = PrivateCosSettings()
    result = settings.default_location_path_template("myfile.json", extra_arg="ignored")
    assert result == "myfile.json"


def test_base_cos_default_client_config_returns_dict(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert isinstance(settings.default_client_config, dict)


def test_base_cos_default_client_config_excludes_bucket_name(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "BUCKET_NAME" not in settings.default_client_config


def test_base_cos_default_client_config_excludes_bucket_endpoint(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "BUCKET_ENDPOINT" not in settings.default_client_config


def test_base_cos_default_client_config_excludes_cos_name(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "COS_NAME" not in settings.default_client_config


def test_base_cos_default_client_config_excludes_verify(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "VERIFY" not in settings.default_client_config


def test_base_cos_default_client_config_excludes_region_name(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "REGION_NAME" not in settings.default_client_config


def test_base_cos_default_client_config_excludes_ecosystem(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert "ECOSYSTEM" not in settings.default_client_config


# ===========================================================================
# PrivateCosSettings
# ===========================================================================

def test_private_cos_bucket_name_loaded_from_env(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert settings.BUCKET_NAME == "my-private-bucket"


def test_private_cos_bucket_endpoint_loaded_from_env(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert settings.BUCKET_ENDPOINT == "https://private.endpoint.com"


def test_private_cos_name_loaded_from_env(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert settings.COS_NAME == "private-cos-name"


def test_private_cos_inherits_templates_path_from_base(private_cos_settings_env):
    settings = PrivateCosSettings()
    assert settings.templates_path.endswith("templates")


# ===========================================================================
# PublicCosSettings
# ===========================================================================

def test_public_cos_bucket_name_loaded_from_env(public_cos_settings_env):
    settings = PublicCosSettings()
    assert settings.BUCKET_NAME == "my-public-bucket"


def test_public_cos_bucket_endpoint_loaded_from_env(public_cos_settings_env):
    settings = PublicCosSettings()
    assert settings.BUCKET_ENDPOINT == "https://public.endpoint.com"


def test_public_cos_name_loaded_from_env(public_cos_settings_env):
    settings = PublicCosSettings()
    assert settings.COS_NAME == "public-cos-name"


def test_public_cos_provider_name_loaded_from_env(public_cos_settings_env):
    settings = PublicCosSettings()
    assert settings.PROVIDER_NAME == "my-provider"


def test_public_cos_path_template_uses_default_provider(public_cos_settings_env):
    settings = PublicCosSettings()
    result = settings.default_location_path_template("file.json")
    assert result == "my-public-bucket/my-provider/file.json"


def test_public_cos_path_template_with_explicit_provider(public_cos_settings_env):
    settings = PublicCosSettings()
    result = settings.default_location_path_template("file.json", provider="custom-provider")
    assert result == "my-public-bucket/custom-provider/file.json"


def test_public_cos_path_template_with_prefix(public_cos_settings_env):
    settings = PublicCosSettings()
    result = settings.default_location_path_template("file.json", prefix="2024/01")
    assert result == "my-public-bucket/my-provider/2024/01/file.json"


def test_public_cos_path_template_with_provider_and_prefix(public_cos_settings_env):
    settings = PublicCosSettings()
    result = settings.default_location_path_template(
        "file.json", provider="custom-provider", prefix="2024/01"
    )
    assert result == "my-public-bucket/custom-provider/2024/01/file.json"


def test_public_cos_path_template_filename_always_at_end(public_cos_settings_env):
    settings = PublicCosSettings()
    result = settings.default_location_path_template(
        "data.parquet", provider="p", prefix="x/y"
    )
    assert result.endswith("data.parquet")


# ===========================================================================
# DataPushSettings
# ===========================================================================

def test_data_push_client_id_loaded_from_env(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.CLIENT_ID == "my-client-id"


def test_data_push_default_max_sleep_crash_time(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.MAX_SLEEP_CRASH_TIME == 5


def test_data_push_default_sleep_crash_time(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.SLEEP_CRASH_TIME == 60.0


def test_data_push_default_max_process_time_out(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.MAX_PROCESS_TIME_OUT == 60.0


def test_data_push_default_env_state_is_dev(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.ENV_STATE == "dev"


def test_data_push_default_tmp_path(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.TMP_PATH == "/tmp"


def test_data_push_default_liveness_file(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.LIVENESS_FILE == "liveness"


def test_data_push_default_is_local_is_false(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.IS_LOCAL is False


def test_data_push_is_dev_env_returns_true_when_dev(data_push_settings_dev_env):
    settings = DataPushSettings()
    assert settings.is_dev_env is True


def test_data_push_is_dev_env_returns_false_when_prod(data_push_settings_prod_env):
    settings = DataPushSettings()
    assert settings.is_dev_env is False


def test_data_push_is_dev_env_returns_false_when_staging(data_push_settings_env):
    with patch.dict("os.environ", {"ENV_STATE": "staging"}):
        settings = DataPushSettings()
        assert settings.is_dev_env is False


def test_data_push_max_sleep_time_default_calculation(data_push_settings_env):
    settings = DataPushSettings()
    assert settings.max_sleep_time == 5 * 60.0


def test_data_push_max_sleep_time_custom_values(data_push_settings_env):
    with patch.dict("os.environ", {"MAX_SLEEP_CRASH_TIME": "10", "SLEEP_CRASH_TIME": "30.0"}):
        settings = DataPushSettings()
        assert settings.max_sleep_time == 300.0


def test_data_push_liveness_path_when_local(data_push_settings_local_env):
    settings = DataPushSettings()
    expected = os.path.join(os.curdir, settings.LIVENESS_FILE)
    assert settings.liveness_path == expected


def test_data_push_liveness_path_when_not_local(data_push_settings_not_local_env):
    settings = DataPushSettings()
    expected = os.path.join("/tmp", settings.LIVENESS_FILE)
    assert settings.liveness_path == expected


def test_data_push_liveness_path_uses_custom_tmp_path(data_push_settings_env):
    with patch.dict("os.environ", {
        "IS_LOCAL": "false",
        "TMP_PATH": "/custom/tmp",
        "LIVENESS_FILE": "health",
    }):
        settings = DataPushSettings()
        assert settings.liveness_path == "/custom/tmp/health"
