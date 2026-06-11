import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from tests.fixtures.internal_application_fixtures import (
    internal_app,
    mock_publication,
    mock_mapped_metadata,
)


# ===========================================================================
# Class attributes
# ===========================================================================

def test_platform_name_is_internal():
    from data_push_cft.output_platform.internal.application import Internal
    assert Internal.__PLATFORM_NAME__ == "INTERNAL"


def test_notify_is_false():
    from data_push_cft.output_platform.internal.application import Internal
    assert Internal.NOTIFY is False


def test_platform_client_class_is_api_publisher_client():
    from data_push_cft.output_platform.internal.application import Internal
    from data_push_cft.output_platform.internal.clients.publisher import ApiPublisherClient
    assert Internal.PLATFORM_CLIENT_CLASS is ApiPublisherClient


def test_consumer_setting_class_is_kafka_consumer_settings():
    from data_push_cft.output_platform.internal.application import Internal
    from data_push_cft.output_platform.internal.settings import KafkaConsumerSettings
    assert Internal.CONSUMER_SETTING_CLASS is KafkaConsumerSettings


# ===========================================================================
# services property
# ===========================================================================

def test_services_property_returns_services(internal_app):
    assert internal_app.services is internal_app._services


# ===========================================================================
# _resolve_action
# ===========================================================================

def test_resolve_action_always_raises_retryable_exception(internal_app):
    from data_push_cft.output_platform.exceptiones import RetryableException
    with pytest.raises(RetryableException):
        internal_app._resolve_action(HTTPException(status_code=400))


def test_resolve_action_raises_for_any_status_code(internal_app):
    from data_push_cft.output_platform.exceptiones import RetryableException
    for status_code in [400, 404, 500, 503]:
        with pytest.raises(RetryableException):
            internal_app._resolve_action(HTTPException(status_code=status_code))


# ===========================================================================
# upload_files
# ===========================================================================

def test_upload_files_returns_list(internal_app, mock_publication, mock_mapped_metadata):
    with patch.object(
        internal_app, "_manager_get_cft_metadata_mapping", return_value=mock_mapped_metadata
    ), patch(
        "data_push_cft.output_platform.internal.application.FileLocation"
    ) as mock_fl, patch(
        "data_push_cft.output_platform.internal.application.PublisherRequestBody"
    ) as mock_prb:
        mock_fl.model_validate.return_value = MagicMock()
        mock_prb.model_validate.return_value = MagicMock()
        result = internal_app.upload_files(mock_publication)

    assert isinstance(result, list)
    assert len(result) == 1


def test_upload_files_calls_manager_get_cft_metadata_mapping(
    internal_app, mock_publication, mock_mapped_metadata
):
    with patch.object(
        internal_app, "_manager_get_cft_metadata_mapping", return_value=mock_mapped_metadata
    ) as mock_manager, patch(
        "data_push_cft.output_platform.internal.application.FileLocation"
    ) as mock_fl, patch(
        "data_push_cft.output_platform.internal.application.PublisherRequestBody"
    ) as mock_prb:
        mock_fl.model_validate.return_value = MagicMock()
        mock_prb.model_validate.return_value = MagicMock()
        internal_app.upload_files(mock_publication)

    mock_manager.assert_called_once_with(
        idf=mock_publication.idf,
        part=mock_publication.part,
        filename=mock_publication.filename
    )


# ===========================================================================
# _manager_get_cft_metadata_mapping
# ===========================================================================

def test_manager_get_cft_metadata_mapping_calls_services(internal_app):
    mock_response = MagicMock()
    internal_app._services.get_cft_metadata_mapping.return_value = mock_response

    result = internal_app._manager_get_cft_metadata_mapping(
        idf="IDF1", part="PART1", filename="file.txt"
    )

    internal_app._services.get_cft_metadata_mapping.assert_called_once_with(
        idf="IDF1", part="PART1", filename="file.txt"
    )
    assert result is mock_response


def test_manager_get_cft_metadata_mapping_calls_resolve_on_http_exception(internal_app):
    internal_app._services.get_cft_metadata_mapping.side_effect = HTTPException(status_code=503)

    from data_push_cft.output_platform.exceptiones import RetryableException
    with pytest.raises(RetryableException):
        internal_app._manager_get_cft_metadata_mapping(
            idf="IDF1", part="PART1", filename="file.txt"
        )


# ===========================================================================
# __init_producer__
# ===========================================================================

def test_init_producer_returns_none(internal_app):
    result = internal_app.__init_producer__()
    assert result is None
