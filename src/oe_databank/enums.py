"""
Enumerations for the OE API. See more at https://services.oxfordeconomics.com/swagger#/.
"""

import enum


class AvalancheSelectionFormat(enum.IntEnum):
    """
    Enum for AvalancheSelectionFormat. Genuinely no idea what each means.

    Members:
        ZERO
        ONE
        TWO
        THREE
        FOUR
        FIVE
        SIX

    """

    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class ListingType(enum.StrEnum):
    """
    Enum for ListingType.

    Members:
        COMPANY: Company.
        HIDDEN: Hidden.
        PRIVATE: Private.
        PUBLIC: Public.
        SHARED: Shared.
    """

    COMPANY = "Company"
    HIDDEN = "Hidden"
    PRIVATE = "Private"
    PUBLIC = "Public"
    SHARED = "Shared"


class FileFormat(enum.IntEnum):
    """
    Enum for FileFormat.

    Members:
        UNKNOWN: Unknown format.
        CSV: Comma-separated values. First line is "sep=,", header row second line, then data after.
    """

    UNKNOWN = 0
    CSV = 1


class Frequency(enum.StrEnum):
    """
    Enum for Frequency.

    Members:
        ANNUAL: Annual.
        MONTHLY: Monthly.
        QUARTERLY: Quarterly.
        BOTH: Both. Tests indicate 'Annual' and 'Quarterly'.
    """

    ANNUAL = "Annual"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    BOTH = "Both"


class Order(enum.StrEnum):
    """
    Enum for Order.

    Members:
        INDICATOR_LOCATION: Indicator then location.
        LOCATION_INDICATOR: Location then indicator.
    """

    INDICATOR_LOCATION = "IndicatorLocation"
    LOCATION_INDICATOR = "LocationIndicator"


class SelectionSortOrder(enum.StrEnum):
    """
    Enum for SelectionSortOrder.

    Members:
        ALPHABETICAL: Alphabetical order.
        TREE: Tree order.
    """

    ALPHABETICAL = "AlphabeticalOrder"
    TREE = "TreeOrder"


class SelectionType(enum.StrEnum):
    """
    Enum for SelectionType.

    Members:
        DATASERIES: Data series selection.
        QUERY: Query selection.
    """

    DATASERIES = "DataSeriesSelection"
    QUERY = "QuerySelection"


class Sequence(enum.StrEnum):
    """
    Enum for Sequence.

    Members:
        EARLIEST_TO_LATEST: Earliest to latest.
        LATEST_TO_EARLIEST: Latest to earliest.
    """

    EARLIEST_TO_LATEST = "EarliestToLatest"
    LATEST_TO_EARLIEST = "LatestToEarliest"
