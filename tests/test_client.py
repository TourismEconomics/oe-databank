from unittest.mock import MagicMock, patch

import httpx
import orjson
import pytest

from oe_databank.client import DatabankClient
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


class TestDatabankClient:
    @pytest.fixture
    def client(self):
        return DatabankClient(api_key="test_api_key")

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
                    variables=[
                        # DownloadRequestVariable(
                        #     variableCode="MRSA!$",
                        #     productTypeCode="GCT",
                        #     measureCodes=[],
                        # )
                    ],
                    regions=[
                        # DownloadRequestRegion(
                        #     databankCode="GCT",
                        #     regionCode="ETH_ADD",
                        # ),
                    ],
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
        assert isinstance(client.raw, httpx.Client)

    @patch("httpx.Client.post")
    def test_download_file_with_request_model(
        self, mock_post, client, download_request
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"mock content"

        response = client.download_file_with_request_model(request=download_request)

        assert response == b"mock content"
        mock_post.assert_called_once()

    @patch("httpx.Client.get")
    def test_download_file_with_selection_id(self, mock_get, client):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"mock content"

        response = client.download_file_with_selection_id(selection_id="123")

        assert response == b"mock content"
        mock_get.assert_called_once_with(
            "/filedownload/123",
            timeout=client.default_download_timeout_seconds,
            follow_redirects=True,
        )

    @patch("httpx.Client.post")
    def test_queue_download_with_request_model(
        self, mock_post, client, download_request
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = (
            b'{"ReadyUrl": "mock_ready_url", "Url": "mock_url"}'
        )

        response = client.queue_download_with_request_model(request=download_request)

        assert isinstance(response, QueueDownloadResponse)
        assert response.ReadyUrl == "mock_ready_url"
        mock_post.assert_called_once()

    @patch("httpx.Client.get")
    def test_check_download_ready_with_id(self, mock_get, client):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"true"

        is_ready = client.check_download_ready_with_id(download_id="123")

        assert is_ready is True
        mock_get.assert_called_once_with("/DownloadReady/123", timeout=None)

    def test_resolve_download_timeout(self, client):
        assert (
            client._resolve_download_timeout(None)
            == client.default_download_timeout_seconds
        )
        assert client._resolve_download_timeout(120) == 120

    def test_resolve_poll_timeout(self, client):
        assert client._resolve_poll_timeout(None) == client.default_poll_timeout_seconds
        assert client._resolve_poll_timeout(300) == 300

    @patch("httpx.Client.get")
    def test_list_databanks(self, mock_get, client):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'[{"name": "Test Databank"}]'

        response = client.list_databanks(as_json=True)

        assert isinstance(response, list)
        assert response[0]["name"] == "Test Databank"
        mock_get.assert_called_once_with(
            "/Databank", timeout=client.default_download_timeout_seconds
        )

    @patch("httpx.Client.post")
    def test_download_paginates_until_short_page(
        self, mock_post, client, download_request
    ):
        page0 = [{"id": i} for i in range(3)]
        page1 = [{"id": i} for i in range(3, 5)]
        r0 = MagicMock()
        r0.status_code = 200
        r0.content = orjson.dumps(page0)
        r1 = MagicMock()
        r1.status_code = 200
        r1.content = orjson.dumps(page1)
        mock_post.side_effect = [r0, r1]

        result = client.download(download_request, page_size=3)

        assert len(result) == 5
        assert result[0]["id"] == 0
        assert result[-1]["id"] == 4
        assert mock_post.call_count == 2
        assert mock_post.call_args_list[0].args[0] == (
            "/download?includemetadata=true&page=0&pagesize=3"
        )
        assert mock_post.call_args_list[1].args[0] == (
            "/download?includemetadata=true&page=1&pagesize=3"
        )

    @patch("httpx.Client.post")
    def test_download_respects_page_limit(self, mock_post, client, download_request):
        page = [{"id": i} for i in range(3)]
        r0 = MagicMock()
        r0.status_code = 200
        r0.content = orjson.dumps(page)
        mock_post.return_value = r0

        result = client.download(download_request, page_size=3, page_limit=1)

        assert len(result) == 3
        assert mock_post.call_count == 1

    @patch("httpx.Client.post")
    def test_download_retries_on_503_then_succeeds(
        self, mock_post, client, download_request
    ):
        client.download_attempts = 3
        client.download_retry_delay_seconds = 0.01

        fail = MagicMock()
        fail.status_code = 503
        fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Server Error",
            request=httpx.Request("POST", "https://example.com/download"),
            response=httpx.Response(503, request=httpx.Request("POST", "https://example.com/download")),
        )

        ok = MagicMock()
        ok.status_code = 200
        ok.content = orjson.dumps([{"id": 1}])
        ok.raise_for_status = MagicMock()
        mock_post.side_effect = [fail, ok]

        result = client.download(download_request, page_size=10)

        assert result == [{"id": 1}]
        assert mock_post.call_count == 2

    @patch("httpx.Client.post")
    def test_download_does_not_retry_on_400(self, mock_post, client, download_request):
        client.download_attempts = 3
        client.download_retry_delay_seconds = 0.01

        bad = MagicMock()
        bad.status_code = 400
        request = httpx.Request("POST", "https://example.com/download")
        response = httpx.Response(400, request=request)
        bad.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=request,
            response=response,
        )
        mock_post.return_value = bad

        with pytest.raises(httpx.HTTPStatusError):
            client.download(download_request, page_size=10)

        assert mock_post.call_count == 1
