"""
Utility functions for the API.
"""

import os

import anyio
import httpx


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
