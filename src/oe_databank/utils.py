"""
Utility functions for the API.
"""

import os
from collections.abc import Mapping
from typing import Any

import anyio
import httpx

from oe_databank.models import FileDownloadRequestDto, Selection


def download_response_to_path(r: httpx.Response, path: os.PathLike):
    """Write a download response to a file."""
    with open(path, "wb") as f:
        for chunk in r.iter_bytes():
            f.write(chunk)


async def download_response_to_path_async(r: httpx.Response, path: os.PathLike):
    """Write a download response to a file."""
    async with await anyio.open_file(path, "wb") as f:
        async for chunk in r.aiter_bytes():
            await f.write(chunk)


def download_path(
    page: int,
    page_size: int,
    *,
    include_metadata: bool = True,
) -> str:
    """Build the `/download` path with pagination query params."""
    return (
        f"/download?includemetadata={str(include_metadata).lower()}"
        f"&page={page}&pagesize={page_size}"
    )


def reached_page_limit(page: int, page_limit: int) -> bool:
    """Return True when `page` has reached a non-negative `page_limit`.

    A `page_limit` of -1 means no limit.
    """
    return page_limit >= 0 and page >= page_limit


def selection_payload(
    selection: Selection | FileDownloadRequestDto | Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize a selection input into a JSON-serializable dict for `/download`.

    `/download` expects a single selection body (not a file-download wrapper).
    """
    if isinstance(selection, Selection):
        return selection.model_dump(mode="json")
    if isinstance(selection, FileDownloadRequestDto):
        if len(selection.selections) != 1:
            raise ValueError(
                "/download accepts a single Selection. Pass a Selection, or a "
                "FileDownloadRequestDto with exactly one selection."
            )
        return selection.selections[0].model_dump(mode="json")
    return dict(selection)
