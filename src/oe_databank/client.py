"""
A synchronous API for interacting with the OE databank.
"""

import os
import time
import warnings

import httpx
import httpx._config
import httpx._types
import orjson
import tenacity

from oe_databank.models import (
    DatabankListResponse,
    FileDownloadRequestDto,
    QueueDownloadResponse,
    RegionResponse,
    TreeResponse,
)
from oe_databank.utils import download_response_to_path

# Request timeout for downloads
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 60
# Total time to wait for a download to be ready
DEFAULT_POLL_TIMEOUT_SECONDS = 120
# Default polling interval
DEFAULT_POLL_INTERVAL_SECONDS = 5.0


class DatabankClient:
    """A synchronous client for interacting with the Oxford Economics databank API.

    ```python
    from oe_databank import (
        DatabankClient,
        FileDownloadRequestDto,
        FileFormat,
        Frequency,
        ListingType,
        Order,
        Selection,
        SelectionSortOrder,
        SelectionType,
        Sequence,
    )

    client = DatabankClient(api_key=...)

    request = FileDownloadRequestDto(
        selections=[
            Selection(
                selectionType=SelectionType.QUERY,
                isTemporarySelection=True,
                databankCode="IST",
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
                startYear=2023,
                endYear=2027,
                precision=5,
                frequency=Frequency.ANNUAL,
                stackedQuarters=False,
            )
        ],
        format=FileFormat.CSV,
        name="test-te-pull",
    )

    client.query(request=request, to_path="result.csv")

    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
        headers: dict | None = None,
        timeout: httpx._types.TimeoutTypes = httpx._config.DEFAULT_TIMEOUT_CONFIG,
        download_timeout_seconds: float | int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
        poll_timeout_seconds: float | int = DEFAULT_POLL_TIMEOUT_SECONDS,
        poll_interval_seconds: float | int = DEFAULT_POLL_INTERVAL_SECONDS,
        download_attempts: int = 3,
        download_retry_delay_seconds: float | int = 1.0,
    ):
        """Initialize the API.

        Args:
            client (httpx.Client, optional): An HTTP client. Defaults to None. If not provided, a client will be created with the provided API key.
            api_key (str, optional): The API key. Defaults to None. Must be provided here or as a header if a client is not provided.
            headers (dict, optional): Additional headers. Defaults to None. If an API key is provided here, it will override the `api_key` attribute.
            timeout (TimeoutTypes, optional): The non-download request timeout. Defaults to httpx._config.DEFAULT_TIMEOUT_CONFIG.
            download_timeout_seconds (float | int, optional): The total time to wait for a download. Defaults to the client's default.
            poll_timeout_seconds (float | int, optional): The total time to wait for a file to be ready. Defaults to the client's default.
            poll_interval_seconds (float | int, optional): The polling interval in seconds. Defaults to the client's default.
            download_attempts (int, optional): The maximum number of download attempts. Defaults to 3.
            download_retry_delay_seconds (float | int, optional): The time to sleep between download retries. Defaults to 1 second.
        """
        self.api_key = api_key
        self.headers = headers or {}
        self._base_url = "https://services.oxfordeconomics.com/api"
        # Define before setting the client
        self.timeout = timeout
        self._client = client or self._make_client()
        self.default_poll_timeout_seconds = poll_timeout_seconds
        self.default_poll_interval_seconds = poll_interval_seconds
        # Download settings
        self.default_download_timeout_seconds = download_timeout_seconds
        self.download_attempts = download_attempts
        self.download_retry_delay_seconds = download_retry_delay_seconds

    @property
    def raw(self) -> httpx.Client:
        """The underlying HTTP client."""
        return self._client

    @property
    def __download_retry_wrapper(self):
        return tenacity.retry(
            stop=tenacity.stop_after_attempt(self.download_attempts),
            wait=tenacity.wait_fixed(self.download_retry_delay_seconds),
            retry=tenacity.retry_if_exception_type(
                (httpx.NetworkError, httpx.TimeoutException)
            ),
        )

    def _make_client(self) -> httpx.Client:
        """Create an HTTP client with the API key in the headers."""
        headers = self.headers.copy()
        if "api-key" in headers:
            if self.api_key is not None:
                warnings.warn(
                    "The 'api-key' header will override the 'api_key' attribute."
                )
        else:
            assert (
                self.api_key is not None
            ), "The API key must be provided as a header or attribute."
            headers["api-key"] = self.api_key
        return httpx.Client(
            base_url=self._base_url, headers=headers, timeout=self.timeout
        )

    def _resolve_download_timeout(self, timeout: float | int | None) -> float | int:
        """Resolve the download timeout. If `None`, use the client's default."""
        if timeout is None:
            return self.default_download_timeout_seconds
        return timeout

    def _resolve_poll_timeout(self, timeout: float | int | None) -> float | int:
        """Resolve the poll timeout. If `None`, use the client's default."""
        if timeout is None:
            return self.default_poll_timeout_seconds
        return timeout

    def _resolve_poll_interval(self, interval: float | int | None) -> float | int:
        """Resolve the poll interval. If `None`, use the client's default."""
        if interval is None:
            return self.default_poll_interval_seconds
        return interval

    def download_file_with_request_model(
        self,
        request: FileDownloadRequestDto,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a file with a file download request in the body."""
        # Must follow redirects as the polling URL is returned until the download is ready.
        r = self.__download_retry_wrapper(self._client.post)(
            "/filedownload",
            content=orjson.dumps(request.model_dump(mode="json")),
            timeout=self._resolve_download_timeout(timeout),
            follow_redirects=True,
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        return r.content

    def download_file_with_selection_id(
        self,
        selection_id: str,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a file by selection ID."""
        path = f"/filedownload/{selection_id}"
        r = self.__download_retry_wrapper(self._client.get)(
            path, timeout=self._resolve_download_timeout(timeout), follow_redirects=True
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        return r.content

    def download_file(
        self,
        *,
        selection_id: str | None = None,
        request: FileDownloadRequestDto | None = None,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a file."""
        assert (
            selection_id or request
        ), "Either 'selection_id' or 'request' must be provided."
        if request:
            return self.download_file_with_request_model(
                request=request, timeout=timeout, to_path=to_path
            )
        else:
            return self.download_file_with_selection_id(
                selection_id=selection_id, timeout=timeout, to_path=to_path
            )

    def queue_download_with_request_model(
        self,
        request: FileDownloadRequestDto,
        timeout: int | None = None,
    ) -> QueueDownloadResponse:
        """Queue a download with a file download request in the body."""
        r = self._client.post(
            "/QueueDownload",
            content=orjson.dumps(request.model_dump(mode="json")),
            timeout=timeout,
        )
        r.raise_for_status()
        return QueueDownloadResponse.model_validate(orjson.loads(r.content))

    def queue_download_with_selection_id(
        self,
        selection_id: str,
        filename: str | None = None,
        timeout: int | None = None,
    ) -> QueueDownloadResponse:
        """Queue a download request by selection ID."""
        path = f"/QueueDownload/{selection_id}" + (f"/{filename}" if filename else "")
        r = self._client.get(path, timeout=timeout)
        r.raise_for_status()
        return QueueDownloadResponse.model_validate(orjson.loads(r.content))

    def queue_download(
        self,
        *,
        selection_id: str | None = None,
        filename: str | None = None,
        request: FileDownloadRequestDto | None = None,
        timeout: int | None = None,
    ) -> QueueDownloadResponse:
        """Queue a download request."""
        assert (
            selection_id or request
        ), "Either 'selection_id' or 'request' must be provided."
        if request:
            return self.queue_download_with_request_model(request, timeout)
        else:
            return self.queue_download_with_selection_id(
                selection_id, filename, timeout
            )

    def check_download_ready_with_id(
        self,
        download_id: str,
        timeout: int | None = None,
    ) -> bool:
        """Check if a download is ready.

        Args:
            download_id (str): The download ID.
            timeout (int, optional): The timeout. Defaults to None.

        Returns:
            bool: Whether the download is ready.
        """
        r = self._client.get(f"/DownloadReady/{download_id}", timeout=timeout)
        r.raise_for_status()
        return orjson.loads(r.content)

    def check_download_ready_with_queue_response(
        self,
        queue_response: QueueDownloadResponse,
        timeout: int | None = None,
    ) -> bool:
        """Check if a download is ready with a queue response.

        Args:
            queue_response (QueueDownloadResponse): The queue response.
            timeout (int, optional): The timeout. Defaults to None.

        Returns:
            bool: Whether the download is ready.
        """
        r = self._client.get(queue_response.ReadyUrl, timeout=timeout)
        r.raise_for_status()
        return orjson.loads(r.content)

    def download_generated_file_with_queue_response(
        self,
        queue_response: QueueDownloadResponse,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a generated file with a queue response.

        Args:
            queue_response (QueueDownloadResponse): The queue response.
            timeout (int, optional): The timeout. Defaults to None.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.

        Returns:
            bytes | None: The file content if `to_path` is not provided.
        """
        r = self._client.get(
            queue_response.Url,
            timeout=self._resolve_download_timeout(timeout),
            follow_redirects=True,
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        return r.content

    def download_generated_file_with_id(
        self,
        download_id: str,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a generated file by download ID.

        Args:
            download_id (str): The download ID.
            timeout (int, optional): The timeout. Defaults to None.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.
        """
        r = self._client.get(
            f"/GenerateLink/{download_id}",
            timeout=self._resolve_download_timeout(timeout),
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        return r.content

    def download_generated_file(
        self,
        *,
        download_id: str | None = None,
        queue_response: QueueDownloadResponse | None = None,
        timeout: int | None = None,
        to_path: os.PathLike | None = None,
    ) -> bytes | None:
        """Download a generated file.

        Args:
            download_id (str, optional): The download ID. Defaults to None.
            queue_response (QueueDownloadResponse, optional): The queue response. Defaults to None.
            timeout (int, optional): The timeout. Defaults to None.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.

        Returns:
            bytes | None: The file content if `to_path` is not provided.
        """
        assert (
            download_id or queue_response
        ), "Either 'download_id' or 'queue_response' must be provided."
        if queue_response:
            return self.download_generated_file_with_queue_response(
                queue_response, timeout=timeout, to_path=to_path
            )
        else:
            return self.download_generated_file_with_id(
                download_id, timeout=timeout, to_path=to_path
            )

    def _poll(
        self,
        queue_response: QueueDownloadResponse,
        timeout: int | None = None,
        poll_timeout_seconds: float | int | None = None,
        poll_interval_seconds: float | int | None = None,
    ) -> bool:
        """Poll a download until it is ready.

        Args:
            queue_response (QueueDownloadResponse): The queue response.
            timeout (int, optional): The request timeout. Defaults to None.
            poll_timeout_seconds (float | int | None, optional): The total time to wait for the download to be ready. Defaults to the client's default.
            poll_interval_seconds (float | int | None, optional): The polling interval in seconds. Defaults to the client's default.

        Returns:
            bool: Whether the download is ready.
        """
        poll_timeout_seconds = self._resolve_poll_timeout(poll_timeout_seconds)
        poll_interval_seconds = self._resolve_poll_interval(poll_interval_seconds)

        start_time = time.time()
        while (time.time() - start_time) < poll_timeout_seconds:
            if self.check_download_ready_with_queue_response(queue_response, timeout):
                return True
            time.sleep(
                min(
                    poll_interval_seconds,
                    poll_timeout_seconds - (time.time() - start_time),
                )
            )
        # Check one last time before returning
        return self.check_download_ready_with_queue_response(queue_response, timeout)

    def query(
        self,
        *,
        selection_id: str | None = None,
        request: FileDownloadRequestDto | None = None,
        to_path: os.PathLike | None = None,
        timeout: int | None = None,
        download_timeout_seconds: float | int | None = None,
        poll_timeout_seconds: float | int | None = None,
        poll_interval_seconds: float | int | None = None,
    ) -> bytes | None:
        """Query the databank for a selection. Must provide either `selection_id` or `request`. If `to_path` is provided, the file will be saved there and `None` will be returned. Otherwise, the file content will be returned as bytes.

        Args:
            selection_id (str, optional): The selection ID. Defaults to None.
            request (FileDownloadRequestDto, optional): The file download request. Defaults to None.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.
            timeout (int, optional): The request timeout. Defaults to None.
            download_timeout_seconds (float | int | None, optional): The total time to wait for the download to be ready. Defaults to the client's default.
            poll_timeout_seconds (float | int | None, optional): The total time to wait for the download to be ready. Defaults to the client's default.
            poll_interval_seconds (float | int | None, optional): The polling interval in seconds. Defaults to the client's default.

        Returns:
            bytes | None: The file content if `to_path` is not provided.
        """
        if request:
            queue_response = self.queue_download_with_request_model(
                request, timeout=timeout
            )
        else:
            queue_response = self.queue_download_with_selection_id(
                selection_id, timeout=timeout
            )
        self._poll(queue_response, timeout, poll_timeout_seconds, poll_interval_seconds)
        return self.download_generated_file(
            queue_response=queue_response,
            timeout=download_timeout_seconds,
            to_path=to_path,
        )

    def list_databanks(
        self,
        to_path: os.PathLike | None = None,
        timeout: int | None = None,
        as_json: bool = False,
    ) -> DatabankListResponse | list[dict] | None:
        """Get a list of all Oxford Economic databanks.

        Args:
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.
            timeout (int, optional): The request timeout. Defaults to the client's default download timeout.
            as_json (bool, optional): Whether to return the response as native JSON types. Defaults to False.

        Returns:
            DatabankListResponse | list[dict] | None: The databank list if `to_path` is not provided. If `as_json` is `True`, the response will be a list of dictionaries.
        """
        r = self._client.get(
            "/Databank", timeout=timeout or self.default_download_timeout_seconds
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        if as_json:
            return orjson.loads(r.content)
        return DatabankListResponse.model_validate(orjson.loads(r.content))

    def get_tree(
        self,
        tree_code: str,
        to_path: os.PathLike | None = None,
        timeout: int | None = None,
        as_json: bool = False,
    ) -> TreeResponse | list[dict] | None:
        """Get the tree metadata for a databank.

        Args:
            tree_code (str): The tree code.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.
            timeout (int, optional): The request timeout. Defaults to the client's default download timeout.
            as_json (bool, optional): Whether to return the response as native JSON types. Defaults to False.

        Returns:
            DatabankTreeResponse | list[dict] | None: The tree metadata if `to_path` is not provided. If `as_json` is `True`, the response will be a list of dictionaries.
        """
        r = self._client.get(
            f"/tree/{tree_code}",
            timeout=timeout or self.default_download_timeout_seconds,
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        if as_json:
            return orjson.loads(r.content)
        return TreeResponse.model_validate(orjson.loads(r.content))

    def get_regions(
        self,
        databank_code: str,
        to_path: os.PathLike | None = None,
        timeout: int | None = None,
        as_json: bool = False,
    ) -> RegionResponse | dict | None:
        """Get the regions of a databank.

        Args:
            databank_code (str): The databank code.
            to_path (os.PathLike, optional): The path to save the file. Defaults to None.
            timeout (int, optional): The request timeout. Defaults to the client's default download timeout.
            as_json (bool, optional): Whether to return the response as native JSON types. Defaults to False.

        Returns:
            RegionResponse | dict | None: The region metadata if `to_path` is not provided. If `as_json` is `True`, the response will be a dictionary.
        """
        r = self._client.get(
            f"/Region/{databank_code}",
            timeout=timeout or self.default_download_timeout_seconds,
        )
        r.raise_for_status()
        if to_path:
            return download_response_to_path(r, to_path)
        if as_json:
            return orjson.loads(r.content)
        return RegionResponse.model_validate(orjson.loads(r.content))
