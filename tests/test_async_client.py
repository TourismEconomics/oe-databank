from unittest.mock import AsyncMock, patch

import httpx
import pytest

from oe_databank.async_client import DatabankAsyncClient
from oe_databank.enums import (
    FileFormat,
    Frequency,
    ListingType,
    Order,
    SelectionSortOrder,
    SelectionType,
    Sequence,
)
from oe_databank.models import FileDownloadRequestDto, QueueDownloadResponse, Selection


class TestDatabankAsyncClient:
    @pytest.fixture
    def client(self):
        return DatabankAsyncClient(api_key="test_api_key")

    @pytest.fixture
    def download_request(self):
        return FileDownloadRequestDto(
            selections=[
                Selection(
                    selectionType=SelectionType.QUERY,
                    isTemporarySelection=True,
                    databankCode="GCT",
                    sequence=Sequence.EARLIEST_TO_LATEST,
                    groupingMode=False,
                    transposeColumns=False,
                    order=Order.LOCATION_INDICATOR,
                    indicatorSortOrder=SelectionSortOrder.ALPHABETICAL,
                    locationSortOrder=SelectionSortOrder.ALPHABETICAL,
                    format=0,
                    legacyDatafeedFileStructure=False,
                    variables=[],
                    regions=[],
                    listingType=ListingType.SHARED,
                    isDataFeed=False,
                    startYear=2015,
                    endYear=2035,
                    precision=5,
                    frequency=Frequency.ANNUAL,
                    stackedQuarters=False,
                )
            ],
            format=FileFormat.CSV,
        )

    def test_init_client_with_api_key(self, client):
        assert client.api_key == "test_api_key"
        assert isinstance(client.raw, httpx.AsyncClient)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_download_file_with_request_model(
        self, mock_post, client, download_request
    ):
        mock_post.return_value = AsyncMock(status_code=200, content=b"mock content")

        response = await client.download_file_with_request_model(
            request=download_request
        )

        assert response == b"mock content"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_download_file_with_selection_id(self, mock_get, client):
        mock_get.return_value = AsyncMock(status_code=200, content=b"mock content")

        response = await client.download_file_with_selection_id(selection_id="123")

        assert response == b"mock content"

        mock_get.assert_called_once_with(
            "/filedownload/123",
            timeout=httpx.USE_CLIENT_DEFAULT,
            follow_redirects=True,
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_queue_download_with_request_model(
        self, mock_post, client, download_request
    ):
        mock_post.return_value = AsyncMock(
            status_code=200,
            content=b'{"ReadyUrl": "mock_ready_url", "Url": "mock_url"}',
        )

        response = await client.queue_download_with_request_model(
            request=download_request
        )

        assert isinstance(response, QueueDownloadResponse)
        assert response.ReadyUrl == "mock_ready_url"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_check_download_ready_with_id(self, mock_get, client):
        mock_get.return_value = AsyncMock(status_code=200, content=b"true")

        is_ready = await client.check_download_ready_with_id(download_id="123")

        assert is_ready is True
        mock_get.assert_called_once_with(
            "/DownloadReady/123", timeout=httpx.USE_CLIENT_DEFAULT
        )

    def test_resolve_download_timeout(self, client):
        assert (
            client._resolve_download_timeout(None)
            == client.default_download_timeout_seconds
        )
        assert client._resolve_download_timeout(120) == 120

    def test_resolve_poll_timeout(self, client):
        assert client._resolve_poll_timeout(None) == client.default_poll_timeout_seconds
        assert client._resolve_poll_timeout(300) == 300

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_list_databanks(self, mock_get, client):
        mock_get.return_value = AsyncMock(
            status_code=200, content=b'[{"name": "Test Databank"}]'
        )

        response = await client.list_databanks(as_json=True)

        assert isinstance(response, list)
        assert response[0]["name"] == "Test Databank"
        mock_get.assert_called_once_with(
            "/Databank", timeout=client.default_download_timeout_seconds
        )
