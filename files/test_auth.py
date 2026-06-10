import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# KafkaProducerSettings
# ---------------------------------------------------------------------------

@pytest.fixture
def kafka_settings_env():
    env = {
        "KAFKA_TOPIC_PUBLIC": "test-topic",
        "KAFKA_TOPIC_PUBLIC_DATA_PUSH_GROUP": "test-group",
    }
    with patch.dict("os.environ", env, clear=False):
        yield env


# ---------------------------------------------------------------------------
# PrivateCosSettings
# ---------------------------------------------------------------------------

@pytest.fixture
def private_cos_settings_env():
    env = {
        "PRIVATE_COS_BUCKET": "my-private-bucket",
        "PRIVATE_COS_BUCKET_ENDPOINT": "https://private.endpoint.com",
        "PRIVATE_COS_NAME": "private-cos-name",
    }
    with patch.dict("os.environ", env, clear=False):
        yield env


# ---------------------------------------------------------------------------
# PublicCosSettings
# ---------------------------------------------------------------------------

@pytest.fixture
def public_cos_settings_env():
    env = {
        "PUBLIC_DATA_PUSH_BUCKET": "my-public-bucket",
        "PUBLIC_DATA_PUSH_BUCKET_ENDPOINT": "https://public.endpoint.com",
        "PUBLIC_DATA_PUSH_COS_NAME": "public-cos-name",
        "API_ETL_PROVIDER_NAME": "my-provider",
    }
    with patch.dict("os.environ", env, clear=False):
        yield env


# ---------------------------------------------------------------------------
# DataPushSettings
# ---------------------------------------------------------------------------

@pytest.fixture
def data_push_settings_env():
    """Minimal required env vars for DataPushSettings."""
    env = {
        "TAASE_MERCURY_CLIENT": "my-client-id",
    }
    with patch.dict("os.environ", env, clear=False):
        yield env


@pytest.fixture
def data_push_settings_dev_env(data_push_settings_env):
    with patch.dict("os.environ", {"ENV_STATE": "dev"}, clear=False):
        yield


@pytest.fixture
def data_push_settings_prod_env(data_push_settings_env):
    with patch.dict("os.environ", {"ENV_STATE": "prod"}, clear=False):
        yield


@pytest.fixture
def data_push_settings_local_env(data_push_settings_env):
    with patch.dict("os.environ", {"IS_LOCAL": "true"}, clear=False):
        yield


@pytest.fixture
def data_push_settings_not_local_env(data_push_settings_env):
    with patch.dict("os.environ", {"IS_LOCAL": "false", "TMP_PATH": "/tmp"}, clear=False):
        yield
