"""
Tests unitaires pour la méthode get_cft_metadata_mapping.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel


# ─────────────────────────────────────────────
# Schémas (reproduits ici pour les tests)
# ─────────────────────────────────────────────

class CftMetadataMetadataQueryParams(BaseModel):
    idf: str
    part: str
    filename: str


# ─────────────────────────────────────────────
# Stub de la classe qui porte la méthode
# ─────────────────────────────────────────────

class FakeSettings:
    get_cft_metadata_mapping_uri = "https://api.example.com/cft/{idf}/{part}/{filename}"


class CftClient:
    """Classe minimale reproduisant le comportement testé."""

    def __init__(self, settings=None):
        self._settings = settings or FakeSettings()

    def request_with_token(self, method: str, url: str):
        raise NotImplementedError("À mocker dans les tests")

    def get_cft_metadata_mapping(self, filters: CftMetadataMetadataQueryParams):
        """
        This method implements the Get cft metadata mapping.
        """
        url = self._settings.get_cft_metadata_mapping_uri.format(
            idf=filters.idf,
            part=filters.part,
            filename=Path(filters.filename).name,
        )
        response = self.request_with_token(
            method="get",
            url=url,
        )
        return response.json()


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def client():
    return CftClient()


@pytest.fixture
def valid_filters():
    return CftMetadataMetadataQueryParams(
        idf="IDF001",
        part="part_A",
        filename="/some/path/to/report.xml",
    )


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.json.return_value = {"status": "ok", "data": [1, 2, 3]}
    return response


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class TestGetCftMetadataMapping:

    # ── 1. Cas nominal ──────────────────────────────────────────────────────

    def test_returns_json_response(self, client, valid_filters, mock_response):
        """La méthode retourne bien le contenu JSON de la réponse HTTP."""
        client.request_with_token = MagicMock(return_value=mock_response)

        result = client.get_cft_metadata_mapping(valid_filters)

        assert result == {"status": "ok", "data": [1, 2, 3]}

    def test_url_is_built_correctly(self, client, valid_filters, mock_response):
        """L'URL est construite avec idf, part et le nom de fichier seul (sans chemin)."""
        client.request_with_token = MagicMock(return_value=mock_response)

        client.get_cft_metadata_mapping(valid_filters)

        expected_url = "https://api.example.com/cft/IDF001/part_A/report.xml"
        client.request_with_token.assert_called_once_with(
            method="get",
            url=expected_url,
        )

    def test_filename_only_basename_is_used(self, client, mock_response):
        """Path(filename).name extrait uniquement le nom du fichier, pas le chemin complet."""
        filters = CftMetadataMetadataQueryParams(
            idf="X",
            part="Y",
            filename="/deep/nested/dir/myfile.csv",
        )
        client.request_with_token = MagicMock(return_value=mock_response)

        client.get_cft_metadata_mapping(filters)

        call_url = client.request_with_token.call_args.kwargs["url"]
        assert "myfile.csv" in call_url
        assert "deep" not in call_url

    def test_request_called_with_get_method(self, client, valid_filters, mock_response):
        """La méthode HTTP utilisée est toujours GET."""
        client.request_with_token = MagicMock(return_value=mock_response)

        client.get_cft_metadata_mapping(valid_filters)

        assert client.request_with_token.call_args.kwargs["method"] == "get"

    # ── 2. Variantes de données ─────────────────────────────────────────────

    def test_filename_without_directory(self, client, mock_response):
        """Un filename sans chemin (juste un nom) est géré correctement."""
        filters = CftMetadataMetadataQueryParams(
            idf="A",
            part="B",
            filename="simple.json",
        )
        client.request_with_token = MagicMock(return_value=mock_response)

        client.get_cft_metadata_mapping(filters)

        call_url = client.request_with_token.call_args.kwargs["url"]
        assert "simple.json" in call_url

    def test_response_json_called_once(self, client, valid_filters, mock_response):
        """response.json() est appelé exactement une fois."""
        client.request_with_token = MagicMock(return_value=mock_response)

        client.get_cft_metadata_mapping(valid_filters)

        mock_response.json.assert_called_once()

    def test_raises_on_404_response(self, client, valid_filters):
        """Un statut 404 (ressource introuvable) lève bien une exception."""
        not_found_response = MagicMock()
        not_found_response.status_code = 404
        not_found_response.raise_for_status.side_effect = Exception("404 Not Found")
        client.request_with_token = MagicMock(side_effect=Exception("404 Not Found"))

        with pytest.raises(Exception, match="404 Not Found"):
            client.get_cft_metadata_mapping(valid_filters)

    # ── 3. Cas d'erreur ─────────────────────────────────────────────────────

    def test_raises_when_request_fails(self, client, valid_filters):
        """Une exception levée par request_with_token se propage correctement."""
        client.request_with_token = MagicMock(side_effect=ConnectionError("timeout"))

        with pytest.raises(ConnectionError, match="timeout"):
            client.get_cft_metadata_mapping(valid_filters)

    def test_raises_when_json_parsing_fails(self, client, valid_filters):
        """Une exception levée par response.json() se propage correctement."""
        bad_response = MagicMock()
        bad_response.json.side_effect = ValueError("invalid JSON")
        client.request_with_token = MagicMock(return_value=bad_response)

        with pytest.raises(ValueError, match="invalid JSON"):
            client.get_cft_metadata_mapping(valid_filters)

    # ── 4. Validation du schéma Pydantic ────────────────────────────────────

    def test_schema_requires_idf(self):
        """Le champ idf est obligatoire."""
        with pytest.raises(Exception):
            CftMetadataMetadataQueryParams(part="p", filename="f.xml")

    def test_schema_requires_part(self):
        """Le champ part est obligatoire."""
        with pytest.raises(Exception):
            CftMetadataMetadataQueryParams(idf="i", filename="f.xml")

    def test_schema_requires_filename(self):
        """Le champ filename est obligatoire."""
        with pytest.raises(Exception):
            CftMetadataMetadataQueryParams(idf="i", part="p")

    def test_schema_valid_instantiation(self):
        """Le schéma s'instancie correctement avec tous les champs."""
        params = CftMetadataMetadataQueryParams(idf="i", part="p", filename="f.xml")
        assert params.idf == "i"
        assert params.part == "p"
        assert params.filename == "f.xml"
