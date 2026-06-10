import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call

from tests.fixtures.event_handler_fixtures import (
    mock_consumer,
    mock_producer,
    mock_publication,
    mock_file_info,
    mock_consumer_settings_class,
    mock_producer_settings_class,
    mock_consumer_class,
    mock_producer_class,
    event_handler,
    event_handler_no_notify,
    event_handler_no_producer,
)


# ===========================================================================
# __init__ — consumer & producer initialization
# ===========================================================================

def test_init_sets_consumer(event_handler, mock_consumer):
    assert event_handler._consumer is mock_consumer


def test_init_sets_producer(event_handler, mock_producer):
    assert event_handler._producer is mock_producer


# ===========================================================================
# consumer / producer properties
# ===========================================================================

def test_consumer_property_returns_consumer(event_handler, mock_consumer):
    assert event_handler.consumer is mock_consumer


def test_producer_property_returns_producer(event_handler, mock_producer):
    assert event_handler.producer is mock_producer


# ===========================================================================
# notify — consumer.commit always called
# ===========================================================================

def test_notify_always_commits_consumer(event_handler, mock_consumer, mock_publication):
    event_handler.notify(publication=mock_publication)
    mock_consumer.commit.assert_called_once()


def test_notify_commits_even_when_no_notify_flag(event_handler_no_notify, mock_consumer, mock_publication):
    event_handler_no_notify.notify(publication=mock_publication)
    mock_consumer.commit.assert_called_once()


# ===========================================================================
# notify — early returns
# ===========================================================================

def test_notify_returns_early_when_notify_false_and_no_error_detail(
    event_handler_no_notify, mock_producer, mock_publication
):
    event_handler_no_notify.notify(publication=mock_publication)
    mock_producer.produce_event.assert_not_called()


def test_notify_does_not_return_early_when_notify_false_but_error_detail_given(
    event_handler_no_notify, mock_producer, mock_publication
):
    with patch.object(event_handler_no_notify, "_serialize_public_event", return_value=MagicMock()):
        event_handler_no_notify.notify(
            publication=mock_publication, error_detail="some error"
        )
    mock_producer.produce_event.assert_called_once()


def test_notify_returns_early_when_no_producer(
    event_handler_no_producer, mock_publication
):
    # Should not raise, just return early
    event_handler_no_producer.notify(publication=mock_publication)


# ===========================================================================
# notify — error_detail sets REJECTED event
# ===========================================================================

def test_notify_sets_rejected_event_when_error_detail(event_handler, mock_publication):
    mock_public_event = MagicMock()
    with patch.object(
        event_handler, "_serialize_public_event", return_value=mock_public_event
    ), patch(
        "data_push_cft.output_platform.base.event_handler.MercuryPublicationEvent"
    ) as mock_event_enum:
        event_handler.notify(publication=mock_publication, error_detail="transfer failed")
        assert mock_public_event.event == mock_event_enum.REJECTED


def test_notify_sets_error_detail_on_event(event_handler, mock_publication):
    mock_public_event = MagicMock()
    with patch.object(
        event_handler, "_serialize_public_event", return_value=mock_public_event
    ), patch("data_push_cft.output_platform.base.event_handler.MercuryPublicationEvent"):
        event_handler.notify(publication=mock_publication, error_detail="transfer failed")
        assert mock_public_event.detail == {"exception": "transfer failed"}


def test_notify_does_not_set_rejected_event_without_error_detail(event_handler, mock_publication):
    mock_public_event = MagicMock()
    with patch.object(event_handler, "_serialize_public_event", return_value=mock_public_event):
        event_handler.notify(publication=mock_publication)
        mock_public_event.event  # should not have been set to REJECTED
        assert "event" not in mock_public_event.__dict__ or mock_public_event.event != "REJECTED"


# ===========================================================================
# notify — produce_event called with correct args
# ===========================================================================

def test_notify_calls_produce_event_with_publication_key(
    event_handler, mock_producer, mock_publication
):
    mock_public_event = MagicMock()
    with patch.object(event_handler, "_serialize_public_event", return_value=mock_public_event):
        event_handler.notify(publication=mock_publication)
    mock_producer.produce_event.assert_called_once_with(
        value=mock_public_event, key=mock_publication.key
    )


def test_notify_uses_empty_list_when_transferred_files_none(event_handler, mock_publication):
    with patch.object(
        event_handler, "_serialize_public_event", return_value=MagicMock()
    ) as mock_serialize:
        event_handler.notify(publication=mock_publication, transferred_files=None)
        mock_serialize.assert_called_once_with(mock_publication, [])


def test_notify_passes_transferred_files_to_serialize(
    event_handler, mock_publication, mock_file_info
):
    with patch.object(
        event_handler, "_serialize_public_event", return_value=MagicMock()
    ) as mock_serialize:
        event_handler.notify(publication=mock_publication, transferred_files=mock_file_info)
        mock_serialize.assert_called_once_with(mock_publication, mock_file_info)


# ===========================================================================
# notify — ProducerDeliveryException → sys.exit
# ===========================================================================

def test_notify_calls_sys_exit_on_producer_delivery_exception(
    event_handler, mock_producer, mock_publication
):
    from bnppam_mercury.core.kafka.exceptions import ProducerDeliveryException

    mock_producer.produce_event.side_effect = ProducerDeliveryException("delivery failed")

    with patch.object(event_handler, "_serialize_public_event", return_value=MagicMock()), \
         patch("data_push_cft.output_platform.base.event_handler.sys.exit") as mock_exit, \
         patch("data_push_cft.output_platform.base.event_handler.logger"):
        event_handler.notify(publication=mock_publication)
        mock_exit.assert_called_once_with(os.EX_SOFTWARE)


# ===========================================================================
# _serialize_public_event
# ===========================================================================

def test_serialize_public_event_returns_serialized_message(
    event_handler, mock_producer, mock_publication
):
    mock_result = MagicMock()
    mock_producer.serialize_message.return_value = mock_result

    result = event_handler._serialize_public_event(mock_publication, [])
    assert result is mock_result


def test_serialize_public_event_calls_producer_serialize_message(
    event_handler, mock_producer, mock_publication
):
    event_handler._serialize_public_event(mock_publication, [])
    mock_producer.serialize_message.assert_called_once_with(mock_publication)


def test_serialize_public_event_with_transferred_files_still_calls_serialize(
    event_handler, mock_producer, mock_publication, mock_file_info
):
    event_handler._serialize_public_event(mock_publication, mock_file_info)
    mock_producer.serialize_message.assert_called_once_with(mock_publication)


# ===========================================================================
# __init_consumer__
# ===========================================================================

def test_init_consumer_returns_consumer_instance(
    mock_consumer_settings_class, mock_consumer_class
):
    from data_push_cft.output_platform.base.event_handler import BaseEventHandler

    class ConcreteHandler(BaseEventHandler):
        CONSUMER_CLASS = mock_consumer_class
        CONSUMER_SETTING_CLASS = mock_consumer_settings_class
        PRODUCER_SETTING_CLASS = MagicMock()

    with patch.object(ConcreteHandler, "__init_producer__", return_value=None):
        handler = ConcreteHandler.__new__(ConcreteHandler)
        handler._producer = None
        result = handler.__init_consumer__()

    mock_consumer_class.assert_called_once()
    assert result is mock_consumer_class.return_value


def test_init_consumer_instantiates_settings(
    mock_consumer_settings_class, mock_consumer_class
):
    from data_push_cft.output_platform.base.event_handler import BaseEventHandler

    class ConcreteHandler(BaseEventHandler):
        CONSUMER_CLASS = mock_consumer_class
        CONSUMER_SETTING_CLASS = mock_consumer_settings_class
        PRODUCER_SETTING_CLASS = MagicMock()

    with patch.object(ConcreteHandler, "__init_producer__", return_value=None):
        handler = ConcreteHandler.__new__(ConcreteHandler)
        handler.__init_consumer__()

    mock_consumer_settings_class.assert_called_once()


# ===========================================================================
# __init_producer__
# ===========================================================================

def test_init_producer_returns_producer_instance(
    mock_producer_settings_class, mock_producer_class
):
    from data_push_cft.output_platform.base.event_handler import BaseEventHandler

    class ConcreteHandler(BaseEventHandler):
        PRODUCER_CLASS = mock_producer_class
        PRODUCER_SETTING_CLASS = mock_producer_settings_class
        CONSUMER_SETTING_CLASS = MagicMock()

    with patch.object(ConcreteHandler, "__init_consumer__", return_value=MagicMock()):
        handler = ConcreteHandler.__new__(ConcreteHandler)
        result = handler.__init_producer__()

    mock_producer_class.assert_called_once()
    assert result is mock_producer_class.return_value


def test_init_producer_returns_none_when_producer_class_is_none(
    mock_producer_settings_class
):
    from data_push_cft.output_platform.base.event_handler import BaseEventHandler

    class ConcreteHandlerNoProd(BaseEventHandler):
        PRODUCER_CLASS = None
        PRODUCER_SETTING_CLASS = mock_producer_settings_class
        CONSUMER_SETTING_CLASS = MagicMock()

    with patch.object(ConcreteHandlerNoProd, "__init_consumer__", return_value=MagicMock()):
        handler = ConcreteHandlerNoProd.__new__(ConcreteHandlerNoProd)
        result = handler.__init_producer__()

    assert result is None


def test_init_producer_instantiates_settings(
    mock_producer_settings_class, mock_producer_class
):
    from data_push_cft.output_platform.base.event_handler import BaseEventHandler

    class ConcreteHandler(BaseEventHandler):
        PRODUCER_CLASS = mock_producer_class
        PRODUCER_SETTING_CLASS = mock_producer_settings_class
        CONSUMER_SETTING_CLASS = MagicMock()

    with patch.object(ConcreteHandler, "__init_consumer__", return_value=MagicMock()):
        handler = ConcreteHandler.__new__(ConcreteHandler)
        handler.__init_producer__()

    mock_producer_settings_class.assert_called_once()
