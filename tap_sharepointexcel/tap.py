"""sharepointexcel tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_sharepointexcel import streams


class Tapsharepointexcel(Tap):
    """sharepointexcel tap class."""

    name = "tap-sharepointexcel"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "start_date",
            th.StringType,
            required=False,
            secret=False,  # Flag config as protected.
            description="Start date",
        ),th.Property(
            "user_agent",
            th.StringType,
            required=False,
            secret=False,  # Flag config as protected.
            description="Broweserless header",
        ),th.Property(
            "access_token",
            th.StringType,
            required=False,
            secret=False,  # Flag config as protected.
            description="Broweserless header",
        ),th.Property(
            "search_query",
            th.StringType,
            required=False,
            secret=False,  # Flag config as protected.
            description="Name of the file to be found in sharepoint. Example: /search(q='XXXXX')",
        )
    ).to_dict()


    def discover_streams(self) -> list[streams.sharepointexcelStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.DriveItemsStream(self),
            streams.ExcelFile(self)
        ]


if __name__ == "__main__":
    Tapsharepointexcel.cli()
