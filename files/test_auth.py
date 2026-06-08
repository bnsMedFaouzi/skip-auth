from unittest.mock import patch

import pytest
from fastapi import HTTPException

from bnppam_mercury.core.internal.services.manager import ManagerServices
from bnppam_mercury.core.internal.services import management_settings as settings
from bnppam_mercury.core.internal.schemas.manager import CftMetadataMetadataResponse

from test.unit.core.fixtures.schemas.manager import (
    cft_metadata_metadata_query_params,
)
from test.unit.core.fixtures.client.internal.manager import (
    get_cft_metadata_mapping_response_ok,
)


# ── 1. Cas nominal ──────────────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient.request_with_token",
    return_value=get_cft_metadata_mapping_response_ok(),
)
def test_get_cft_metadata_mapping_ok(_mock, cft_metadata_metadata_query_params):
    service = ManagerServices(settings)

    response = service.get_cft_metadata_mapping(
        idf=cft_metadata_metadata_query_params.idf,
        part=cft_metadata_metadata_query_params.part,
        filename=cft_metadata_metadata_query_params.filename,
    )

    assert isinstance(response, CftMetadataMetadataResponse)
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
    target="bnppam_mercury.core.client.http.HttpClient.request_with_token",
    return_value=get_cft_metadata_mapping_response_ok(),
)
def test_get_cft_metadata_mapping_pivot_business_scope_default(_mock, cft_metadata_metadata_query_params):
    """business_scope vaut '' par défaut si absent."""
    service = ManagerServices(settings)

    response = service.get_cft_metadata_mapping(
        idf=cft_metadata_metadata_query_params.idf,
        part=cft_metadata_metadata_query_params.part,
        filename=cft_metadata_metadata_query_params.filename,
    )

    assert isinstance(response, CftMetadataMetadataResponse)
    assert response.metadata.pivots[0].business_scope == ""


# ── 3. Cas d'erreur ─────────────────────────────────────────────────────

@patch(
    target="bnppam_mercury.core.client.http.HttpClient.request_with_token",
    side_effect=HTTPException(status_code=500, detail="Internal Server Error"),
)
def test_get_cft_metadata_mapping_ko(_mock, cft_metadata_metadata_query_params):
    service = ManagerServices(settings)

    with pytest.raises(HTTPException) as ex:
        service.get_cft_metadata_mapping(
            idf=cft_metadata_metadata_query_params.idf,
            part=cft_metadata_metadata_query_params.part,
            filename=cft_metadata_metadata_query_params.filename,
        )

    assert ex.value.status_code == 500
    assert ex.value.detail == "Internal Server Error"


@patch(
    target="bnppam_mercury.core.client.http.HttpClient.request_with_token",
    side_effect=HTTPException(status_code=404, detail="No mapping found"),
)
def test_get_cft_metadata_mapping_not_found(_mock, cft_metadata_metadata_query_params):
    service = ManagerServices(settings)

    with pytest.raises(HTTPException) as ex:
        service.get_cft_metadata_mapping(
            idf=cft_metadata_metadata_query_params.idf,
            part=cft_metadata_metadata_query_params.part,
            filename=cft_metadata_metadata_query_params.filename,
        )

    assert ex.value.status_code == 404
    assert ex.value.detail == "No mapping found"
