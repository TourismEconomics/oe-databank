from oe_databank.enums import (
    FileFormat,
    Frequency,
    ListingType,
    Order,
    SelectionSortOrder,
    SelectionType,
    Sequence,
)
from oe_databank.models import (
    DownloadRequestRegion,
    DownloadRequestVariable,
    FileDownloadRequestDto,
    Selection,
)


class TestFileDownloadRequestDto:

    def test_init_whole_databank(self):
        FileDownloadRequestDto(
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
                    startYear=2000,
                    endYear=2001,
                    precision=5,
                    frequency=Frequency.ANNUAL,
                    stackedQuarters=False,
                )
            ],
            format=FileFormat.CSV,
        )

    def test_init_partial_databank(self):
        FileDownloadRequestDto(
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
                        DownloadRequestVariable(
                            variableCode="MRSA!$",
                            productTypeCode="GCT",
                            measureCodes=[],
                        )
                    ],
                    regions=[
                        DownloadRequestRegion(
                            databankCode="GCT",
                            regionCode="ETH_ADD",
                        ),
                    ],
                    listingType=ListingType.SHARED,
                    isDataFeed=False,
                    startYear=2000,
                    endYear=2001,
                    precision=5,
                    frequency=Frequency.ANNUAL,
                    stackedQuarters=False,
                )
            ],
            format=FileFormat.CSV,
        )
