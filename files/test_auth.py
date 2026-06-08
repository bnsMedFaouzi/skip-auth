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

    response = client.get_cft_metadata_mapping(
        idf=cft_metadata_metadata_query_params.idf,
        part=cft_metadata_metadata_query_params.part,
        filename=cft_metadata_metadata_query_params.filename,
    )

    assert response is not None
    assert response.metadata is not None
    assert response.metadata.flow == "flow_test"
    assert response.metadata.publisher == "publisher_test"
    assert response.metadata.correlationID == "corr-001"
    assert response.metadata.metadata_filename == "metadata_test.xml"
    assert len(response.metadata.pivots) == 1
    assert response.metadata.pivots[0].name == "pivot_test"
    assert response.metadata.pivots[0].version == "1.0"
    assert response.metadata.pivots[0].file_path == "/some/path/report.xml"
    assert response.publication_type.name == "publication_type_test"


# ── 2. Variantes de données ─────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_ok(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_returns_cft_metadata_response_type(_mock, _mock1, cft_metadata_metadata_query_params):
    """La réponse est bien validée en CftMetadataMetadataResponse via model_validate."""
    from bnppam_mercury.core.internal.schemas.manager import CftMetadataMetadataResponse

    client = ManagerClient(settings)

    response = client.get_cft_metadata_mapping(
        idf=cft_metadata_metadata_query_params.idf,
        part=cft_metadata_metadata_query_params.part,
        filename=cft_metadata_metadata_query_params.filename,
    )

    assert isinstance(response, CftMetadataMetadataResponse)


@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    return_value=get_cft_metadata_mapping_response_ok(),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_pivot_business_scope_default(_mock, _mock1, cft_metadata_metadata_query_params):
    """business_scope vaut '' par défaut si absent."""
    client = ManagerClient(settings)

    response = client.get_cft_metadata_mapping(
        idf=cft_metadata_metadata_query_params.idf,
        part=cft_metadata_metadata_query_params.part,
        filename=cft_metadata_metadata_query_params.filename,
    )

    assert response.metadata.pivots[0].business_scope == ""


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
        client.get_cft_metadata_mapping(
            idf=cft_metadata_metadata_query_params.idf,
            part=cft_metadata_metadata_query_params.part,
            filename=cft_metadata_metadata_query_params.filename,
        )

    assert ex.value.status_code == 404
    assert ex.value.detail == error_message


@patch(
    target="bnppam_mercury.core.client.http.HttpClient._request",
    side_effect=HTTPException(
        status_code=500,
        detail="Request failed, status code: 500, due to detail: {'detail': 'Internal Server Error'}",
    ),
)
@patch(
    target="bnppam_mercury.core.internal.client.manager.ManagerClient.GET_TAASE_TOKEN_FUNCTION",
    return_value="<access_token>",
)
def test_get_cft_metadata_mapping_ko(_mock, _mock1, cft_metadata_metadata_query_params):
    client = ManagerClient(settings)

    message_error = "Request failed, status code: 500, due to detail: {'detail': 'Internal Server Error'}"

    with pytest.raises(HTTPException) as ex:
        client.get_cft_metadata_mapping(
            idf=cft_metadata_metadata_query_params.idf,
            part=cft_metadata_metadata_query_params.part,
            filename=cft_metadata_metadata_query_params.filename,
        )

    assert ex.value.status_code == 500
    assert ex.value.detail == message_error
