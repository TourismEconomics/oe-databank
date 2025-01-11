# oe-databank

[![PyPI version](https://img.shields.io/pypi/v/oe-databank?color=fe7200&labelColor=eeeeee)](https://pypi.python.org/pypi/oe-databank/)
![GitHub stars](https://img.shields.io/github/stars/tourismeconomics/oe-databank?color=fe7200&labelColor=eeeeee)

Python expression of Oxford Economics' Databank API.

## Installation

```bash
pip install oe-databank
```

## Usage

Queries can be sent synchronously or asynchronously.

```python
import asyncio
from oe_databank import (
    DatabankAsyncClient,
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

DatabankClient(api_key=...).query(request=request, to_path="sync_result.csv")

asyncio.run(DatabankAsyncClient(api_key=...).query(request=request, to_path="async_result.csv"))
```

You might run into issues with large downloads, so you can use retry options to handle errors during download.

```python
from oe_databank import DatabankClient

DatabankClient(api_key=...).query(
    request=request,
    to_path="sync_result.csv",
    download_attempts=3,
    download_retry_delay_seconds=2.0,
)
```
