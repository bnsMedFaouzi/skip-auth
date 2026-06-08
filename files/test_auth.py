from unittest.mock import patch

import pytest
from fastapi import HTTPException

from bnppam_mercury.core.internal.services.manager import ManagerClient
from bnppam_mercury.core.internal.services import management_settings as settings

from test.unit.core.fixtures.schemas.manager import (
    cft_metadata_metadata_query_params,
)
from test.unit.core.fixtures.client.internal.manager import (
    get_cft_metadata_mapping_response_ok,
    get_cft_metadata_mapping_response_404,
)


# ── 1. Cas nominal ──────────────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_ok(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_ok(_mock, _mock1, cft_metadata_metadata_query_params):
    client = ManagerClient(settings)

    response = client.get_cft_metadata_mapping(filters=cft_metadata_metadata_query_params)

    assert response is not None


# ── 2. Variantes de données ─────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_ok(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_called_with_get_method(_mock, _mock1, cft_metadata_metadata_query_params):
    client = ManagerClient(settings)

    client.get_cft_metadata_mapping(filters=cft_metadata_metadata_query_params)

    assert _mock1.call_args.kwargs.get("method", "get") == "get"


@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_ok(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_filename_basename_only(_mock, _mock1, cft_metadata_metadata_query_params):
    """Seul le nom du fichier (sans chemin) est utilisé dans l'URL."""
    client = ManagerClient(settings)

    response = client.get_cft_metadata_mapping(filters=cft_metadata_metadata_query_params)

    assert response is not None


# ── 3. Cas d'erreur ─────────────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_404(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_not_found(_mock, _mock1, cft_metadata_metadata_query_params):
    client = ManagerClient(settings)

    error_message = "Request failed, status code: 404, due to detail: {'detail': 'No mapping found'}"

    with pytest.raises(HTTPException) as ex:
        client.get_cft_metadata_mapping(filters=cft_metadata_metadata_query_params)

    assert ex.value.status_code == 404
    assert ex.value.detail == error_message


@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    side_effect=HTTPException(status_code=500, detail="Request failed, status code: 500, due to detail: {'detail': 'Internal Server Error'}"),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_ko(_mock, _mock1, cft_metadata_metadata_query_params):
    client = ManagerClient(settings)

    message_error = "Request failed, status code: 500, due to detail: {'detail': 'Internal Server Error'}"

    with pytest.raises(HTTPException) as ex:
        client.get_cft_metadata_mapping(filters=cft_metadata_metadata_query_params)

    assert ex.value.status_code == 500
    assert ex.value.detail == message_error
