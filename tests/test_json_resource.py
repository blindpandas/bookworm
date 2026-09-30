from __future__ import annotations

import re
import warnings
from unittest.mock import Mock, patch

import pytest
import requests
from pydantic import BaseModel, Field
from pydantic.warnings import PydanticDeprecatedSince20

from bookworm.http_tools.json_resource import RemoteJsonResource


class SampleModel(BaseModel):
    id: int
    name: str
    tags: list[str] = Field(default_factory=list)


def test_parse_data_success():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    data = {"id": 1, "name": "Bookworm", "tags": ["reader", "a11y"]}
    result = resource.parse_data(data)
    assert isinstance(result, SampleModel)
    assert result.id == 1
    assert result.name == "Bookworm"
    assert result.tags == ["reader", "a11y"]


def test_parse_data_no_pydantic_deprecated_warning():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    data = {"id": 42, "name": "Test"}
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        result = resource.parse_data(data)
        assert result.id == 42
        deprecated_warnings = [
            w for w in recorded_warnings if issubclass(w.category, PydanticDeprecatedSince20)
        ]
        assert len(deprecated_warnings) == 0


def test_parse_data_validation_error():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    invalid_data = {"id": "not-an-int", "name": 123, "tags": "not-a-list"}
    with pytest.raises(ValueError, match="Failed to parse data"):
        resource.parse_data(invalid_data)


def test_request_data_success():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    mock_response = Mock()
    mock_response.json.return_value = {"id": 1, "name": "Valid"}
    with patch("requests.get", return_value=mock_response) as mock_get:
        data = resource.request_data()
        assert data == {"id": 1, "name": "Valid"}
        mock_get.assert_called_once_with("https://example.com/data.json")


def test_request_data_connection_error():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    with (
        patch("requests.get", side_effect=requests.RequestException("Network down")),
        pytest.raises(
            ConnectionError, match=re.escape("Failed to get url https://example.com/data.json")
        ),
    ):
        resource.request_data()


def test_request_data_json_decode_error():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    with (
        patch("requests.get", return_value=mock_response),
        pytest.raises(ValueError, match="Failed to parse JSON data"),
    ):
        resource.request_data()


def test_get_success_without_deprecated_warning():
    resource = RemoteJsonResource(url="https://example.com/data.json", model=SampleModel)
    mock_response = Mock()
    mock_response.json.return_value = {"id": 99, "name": "Integrated"}
    with (
        patch("requests.get", return_value=mock_response),
        warnings.catch_warnings(record=True) as recorded_warnings,
    ):
        warnings.simplefilter("always")
        result = resource.get()
        assert isinstance(result, SampleModel)
        assert result.id == 99
        assert result.name == "Integrated"
        deprecated_warnings = [
            w for w in recorded_warnings if issubclass(w.category, PydanticDeprecatedSince20)
        ]
        assert len(deprecated_warnings) == 0
