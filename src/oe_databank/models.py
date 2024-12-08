"""
API data models for the databank. See more at https://services.oxfordeconomics.com/swagger#/.

"""

import datetime

from pydantic import BaseModel, Field, RootModel

from oe_databank.enums import (
    FileFormat,
    Frequency,
    ListingType,
    Order,
    SelectionSortOrder,
    SelectionType,
    Sequence,
)


class DownloadRequestRegion(BaseModel):
    """A region definition passed in a download request."""

    databankCode: str | None
    regionCode: str | None


class DownloadRequestVariable(BaseModel):
    """A variable definition passed in a download request."""

    variableCode: str | None
    productTypeCode: str | None
    measureCodes: list[str]


class Selection(BaseModel):
    """A databank selection. Nullable columns default to None."""

    downloadUrl: str | None = Field(default=None, exclude=True)
    id: str | None = Field(default=None, exclude=True)
    selectionType: SelectionType
    lastUpdate: datetime.datetime | None = Field(default=None, exclude=True)
    isTemporarySelection: bool
    databankCode: str | None = None
    sequence: Sequence
    groupingMode: bool
    transposeColumns: bool | None = None
    order: Order
    indicatorSortOrder: SelectionSortOrder
    locationSortOrder: SelectionSortOrder
    sortedColumnName: str | None = None
    sortedColumnOrder: str | None = None
    format: int
    legacyDatafeedFileStructure: bool
    variables: list[DownloadRequestVariable] = Field(default_factory=list)
    regions: list[DownloadRequestRegion] = Field(default_factory=list)
    contactId: str | None = Field(default=None, exclude=True)
    listingType: ListingType
    isDataFeed: bool
    name: str | None = None
    startYear: int
    endYear: int
    precision: int
    frequency: Frequency
    stackedQuarters: bool


class FileDownloadRequestDto(BaseModel):
    """A request to query multiple selections and download the results as a file."""

    selections: list[Selection] = Field(min_length=1)
    format: FileFormat
    name: str | None = None


class QueueDownloadResponse(BaseModel):
    """A response from the /QueueDownload endpoint."""

    Url: str
    ReadyUrl: str


class TreeMetadata(BaseModel):
    """The metadata for a tree in the databank."""

    Name: str
    TreeCode: str
    Url: str


class ColumnMetadata(BaseModel):
    """The metadata for a column in the databank."""

    ColumnName: str
    DisplayOrder: int
    MetadataFieldName: str


class DatabankMetadata(BaseModel):
    """The metadata for a databank."""

    Name: str
    Url: str
    DatabankCode: str
    StartYear: int
    EndYear: int
    HasQuarterlyData: bool
    Trees: list[TreeMetadata]
    MapUrl: str
    DatabankColumns: list[ColumnMetadata]
    HasAccess: bool


class DatabankListResponse(RootModel):
    """The response from the /Databank endpoint."""

    root: list[DatabankMetadata]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)


class TreeNode(BaseModel):
    """A node in the databank tree."""

    Name: str
    Code: str
    ProductTypeCode: str
    DisplayOrder: int
    HasAccess: bool
    Children: list["TreeNode"] = Field(default_factory=list)


class TreeResponse(RootModel):
    """The response from the /DatabankTree endpoint."""

    root: list[TreeNode]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)


class RegionMetadata(BaseModel):
    """The metadata for a region in the databank."""

    RegionCode: str
    Name: str
    DatabankCode: str
    DisplayOrder: int
    HasAccess: bool


class RegionResponse(BaseModel):
    """The response from the /Region endpoint."""

    Regions: list[RegionMetadata]
