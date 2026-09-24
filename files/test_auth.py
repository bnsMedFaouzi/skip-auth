# tests/test_log_event.py
import pytest
from unittest.mock import MagicMock, patch, call


# --- Helpers ---

def make_handler():
    """Instancie BaseEventHandler avec les dépendances mockées."""
    handler = BaseEventHandler.__new__(BaseEventHandler)
    handler.__init_log_events_client__ = MagicMock()
    return handler

def make_publication(metadata="meta", publication_type="type_a"):
    pub = MagicMock()
    pub.metadata = metadata
    pub.publication_type = publication_type
    return pub


# --- Tests log_event ---

def test_log_event_warns_and_returns_when_no_client():
    handler = make_handler()
    handler.__init_log_events_client__.return_value = None
    publication = make_publication()

    with patch("path.to.module.logger.logger_") as mock_logger:
        handler.log_event(publication, client_id="client_1", event_type="EVENT")
        mock_logger.warning.assert_called_once_with("No Log Events Client initialized")


def test_log_event_does_not_push_when_no_client():
    handler = make_handler()
    handler.__init_log_events_client__.return_value = None
    publication = make_publication()

    handler.log_event(publication, client_id="client_1", event_type="EVENT")
    # Pas d'appel à push_events


def test_log_event_calls_push_events_with_correct_args():
    handler = make_handler()
    mock_client = MagicMock()
    handler.__init_log_events_client__.return_value = mock_client
    publication = make_publication(metadata="meta_x", publication_type="type_b")

    with patch("path.to.module.Publication") as MockPublication:
        mock_pub_instance = MagicMock()
        MockPublication.return_value = mock_pub_instance

        handler.log_event(publication, client_id="client_1", event_type="EVENT_TYPE")

        MockPublication.assert_called_once_with(
            metadata="meta_x",
            publication_type="type_b",
        )
        mock_client.push_events.assert_called_once_with(
            client_id="client_1",
            publication=mock_pub_instance,
            event_type="EVENT_TYPE",
        )


def test_log_event_logs_error_on_exception():
    handler = make_handler()
    mock_client = MagicMock()
    mock_client.push_events.side_effect = Exception("push failed")
    handler.__init_log_events_client__.return_value = mock_client
    publication = make_publication()

    with patch("path.to.module.logger.logger_") as mock_logger:
        with patch("path.to.module.Publication"):
            handler.log_event(publication, client_id="client_1", event_type="EVENT")
            mock_logger.error.assert_called_once()


def test_log_event_does_not_raise_on_exception():
    handler = make_handler()
    mock_client = MagicMock()
    mock_client.push_events.side_effect = Exception("push failed")
    handler.__init_log_events_client__.return_value = mock_client
    publication = make_publication()

    with patch("path.to.module.logger.logger_"):
        with patch("path.to.module.Publication"):
            # Ne doit pas lever d'exception (non-blocking)
            handler.log_event(publication, client_id="client_1", event_type="EVENT")
