import os
import pytest
from unittest.mock import patch

from output_platform.settings import (
    KafkaProducerSettings,
    BaseCosSettings,
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

class TestKafkaProducerSettings:

    def test_topic_name_loaded_from_env(self, kafka_settings_env):
        settings = KafkaProducerSettings()
        assert settings.TOPIC_NAME == "test-topic"

    def test_group_name_loaded_from_env(self, kafka_settings_env):
        settings = KafkaProducerSettings()
        assert settings.GROUP_NAME == "test-group"

    def test_topic_name_alias_is_kafka_topic_public(self, kafka_settings_env):
        settings = KafkaProducerSettings()
        dumped = settings.model_dump(by_alias=True)
        assert "KAFKA_TOPIC_PUBLIC" in dumped

    def test_group_name_alias_is_kafka_group(self, kafka_settings_env):
        settings = KafkaProducerSettings()
        dumped = settings.model_dump(by_alias=True)
        assert "KAFKA_TOPIC_PUBLIC_DATA_PUSH_GROUP" in dumped


# ===========================================================================
# BaseCosSettings  (tested via PrivateCosSettings — concrete subclass)
# ===========================================================================

class TestBaseCosSettings:

    def test_templates_path_is_absolute(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert os.path.isabs(settings.templates_path)

    def test_templates_path_ends_with_templates(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert settings.templates_path.endswith("templates")

    def test_default_location_path_template_returns_filename(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        result = settings.default_location_path_template("myfile.json")
        assert result == "myfile.json"

    def test_default_location_path_template_ignores_kwargs(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        result = settings.default_location_path_template("myfile.json", extra_arg="ignored")
        assert result == "myfile.json"

    def test_default_client_config_excludes_bucket_name(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "BUCKET_NAME" not in config

    def test_default_client_config_excludes_bucket_endpoint(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "BUCKET_ENDPOINT" not in config

    def test_default_client_config_excludes_cos_name(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "COS_NAME" not in config

    def test_default_client_config_excludes_verify(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "VERIFY" not in config

    def test_default_client_config_excludes_region_name(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "REGION_NAME" not in config

    def test_default_client_config_excludes_ecosystem(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        config = settings.default_client_config
        assert "ECOSYSTEM" not in config

    def test_default_client_config_returns_dict(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert isinstance(settings.default_client_config, dict)


# ===========================================================================
# PrivateCosSettings
# ===========================================================================

class TestPrivateCosSettings:

    def test_bucket_name_loaded_from_env(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert settings.BUCKET_NAME == "my-private-bucket"

    def test_bucket_endpoint_loaded_from_env(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert settings.BUCKET_ENDPOINT == "https://private.endpoint.com"

    def test_cos_name_loaded_from_env(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert settings.COS_NAME == "private-cos-name"

    def test_inherits_templates_path_from_base(self, private_cos_settings_env):
        settings = PrivateCosSettings()
        assert settings.templates_path.endswith("templates")


# ===========================================================================
# PublicCosSettings
# ===========================================================================

class TestPublicCosSettings:

    def test_bucket_name_loaded_from_env(self, public_cos_settings_env):
        settings = PublicCosSettings()
        assert settings.BUCKET_NAME == "my-public-bucket"

    def test_bucket_endpoint_loaded_from_env(self, public_cos_settings_env):
        settings = PublicCosSettings()
        assert settings.BUCKET_ENDPOINT == "https://public.endpoint.com"

    def test_cos_name_loaded_from_env(self, public_cos_settings_env):
        settings = PublicCosSettings()
        assert settings.COS_NAME == "public-cos-name"

    def test_provider_name_loaded_from_env(self, public_cos_settings_env):
        settings = PublicCosSettings()
        assert settings.PROVIDER_NAME == "my-provider"

    def test_path_template_uses_default_provider(self, public_cos_settings_env):
        settings = PublicCosSettings()
        result = settings.default_location_path_template("file.json")
        assert result == "my-public-bucket/my-provider/file.json"

    def test_path_template_with_explicit_provider(self, public_cos_settings_env):
        settings = PublicCosSettings()
        result = settings.default_location_path_template(
            "file.json", provider="custom-provider"
        )
        assert result == "my-public-bucket/custom-provider/file.json"

    def test_path_template_with_prefix(self, public_cos_settings_env):
        settings = PublicCosSettings()
        result = settings.default_location_path_template("file.json", prefix="2024/01")
        assert result == "my-public-bucket/my-provider/2024/01/file.json"

    def test_path_template_with_provider_and_prefix(self, public_cos_settings_env):
        settings = PublicCosSettings()
        result = settings.default_location_path_template(
            "file.json", provider="custom-provider", prefix="2024/01"
        )
        assert result == "my-public-bucket/custom-provider/2024/01/file.json"

    def test_path_template_filename_always_at_end(self, public_cos_settings_env):
        settings = PublicCosSettings()
        result = settings.default_location_path_template(
            "data.parquet", provider="p", prefix="x/y"
        )
        assert result.endswith("data.parquet")


# ===========================================================================
# DataPushSettings
# ===========================================================================

class TestDataPushSettings:

    def test_client_id_loaded_from_env(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.CLIENT_ID == "my-client-id"

    # --- default values ---

    def test_default_max_sleep_crash_time(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.MAX_SLEEP_CRASH_TIME == 5

    def test_default_sleep_crash_time(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.SLEEP_CRASH_TIME == 60.0

    def test_default_max_process_time_out(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.MAX_PROCESS_TIME_OUT == 60.0

    def test_default_env_state_is_dev(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.ENV_STATE == "dev"

    def test_default_tmp_path(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.TMP_PATH == "/tmp"

    def test_default_liveness_file(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.LIVENESS_FILE == "liveness"

    def test_default_is_local_is_false(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.IS_LOCAL is False

    # --- is_dev_env property ---

    def test_is_dev_env_returns_true_when_dev(self, data_push_settings_dev_env):
        settings = DataPushSettings()
        assert settings.is_dev_env is True

    def test_is_dev_env_returns_false_when_prod(self, data_push_settings_prod_env):
        settings = DataPushSettings()
        assert settings.is_dev_env is False

    def test_is_dev_env_returns_false_when_staging(self, data_push_settings_env):
        with patch.dict("os.environ", {"ENV_STATE": "staging"}):
            settings = DataPushSettings()
            assert settings.is_dev_env is False

    # --- max_sleep_time property ---

    def test_max_sleep_time_default_calculation(self, data_push_settings_env):
        settings = DataPushSettings()
        assert settings.max_sleep_time == 5 * 60.0

    def test_max_sleep_time_custom_values(self, data_push_settings_env):
        with patch.dict("os.environ", {
            "MAX_SLEEP_CRASH_TIME": "10",
            "SLEEP_CRASH_TIME": "30.0",
        }):
            settings = DataPushSettings()
            assert settings.max_sleep_time == 300.0

    # --- liveness_path property ---

    def test_liveness_path_when_local(self, data_push_settings_local_env):
        settings = DataPushSettings()
        expected = os.path.join(os.curdir, settings.LIVENESS_FILE)
        assert settings.liveness_path == expected

    def test_liveness_path_when_not_local(self, data_push_settings_not_local_env):
        settings = DataPushSettings()
        expected = os.path.join("/tmp", settings.LIVENESS_FILE)
        assert settings.liveness_path == expected

    def test_liveness_path_uses_tmp_path_when_not_local(self, data_push_settings_env):
        with patch.dict("os.environ", {
            "IS_LOCAL": "false",
            "TMP_PATH": "/custom/tmp",
            "LIVENESS_FILE": "health",
        }):
            settings = DataPushSettings()
            assert settings.liveness_path == "/custom/tmp/health"
