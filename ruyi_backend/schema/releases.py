import datetime

from pydantic import BaseModel


class ReleaseDetailV1(BaseModel):
    """Detailed information for a release."""

    version: str
    """Version string."""
    channel: str
    """Release channel."""

    release_date: datetime.datetime
    """Release date."""

    download_urls: dict[str, list[str]]
    """Download URLs for this release. The key is the OS and architecture combo
    as defined by the RuyiSDK Package Manager normalization logic, e.g.
    "linux/x86_64", "linux/aarch64", "windows/x86_64", etc.
    """


class LatestReleasesV1(BaseModel):
    """Latest releases info."""

    channels: dict[str, ReleaseDetailV1]
    """Latest release info keyed by release channel."""
