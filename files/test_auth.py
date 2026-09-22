"""
Simple class to open an S3/COS file just like Python's native open(),
with clean error handling for common failure cases (missing file, bad
credentials, connection issues, etc.).
"""

import logging

import s3fs

logger = logging.getLogger(__name__)


class S3FileNotFoundError(Exception):
    """The requested file does not exist in the bucket."""


class S3AuthError(Exception):
    """Authentication or permission error."""


class S3ConnectionError(Exception):
    """Connection error to the S3/COS endpoint."""


class S3Client:
    """
    Minimal S3/COS client: used just like Python's native `open()`.

    Example
    -------
    >>> client = S3Client(
    ...     endpoint_url="https://s3.eu-fr2.cloud-object-storage.appdomain.cloud",
    ...     access_key="...",
    ...     secret_key="...",
    ... )
    >>> with client.open("my-bucket/path/file.csv") as f:
    ...     content = f.read()
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str | None = None,
    ):
        self.fs = s3fs.S3FileSystem(
            key=access_key,
            secret=secret_key,
            client_kwargs={
                "endpoint_url": endpoint_url,
                **({"region_name": region_name} if region_name else {}),
            },
            config_kwargs={"s3": {"addressing_style": "path"}},
        )

    def open(self, path: str, mode: str = "rb", block_size: int = 8 * 1024 * 1024):
        """
        Open an S3 file, used like the native open() (context manager included).

        Raises:
        - S3FileNotFoundError if the file does not exist
        - S3AuthError if credentials/permissions are invalid
        - S3ConnectionError for any other network/connection issue
        """
        try:
            return self.fs.open(path, mode=mode, block_size=block_size)
        except FileNotFoundError as e:
            raise S3FileNotFoundError(f"File not found: {path}") from e
        except PermissionError as e:
            raise S3AuthError(f"Access denied: {path}") from e
        except Exception as e:
            raise S3ConnectionError(f"Error opening {path}: {e}") from e

    def exists(self, path: str) -> bool:
        return self.fs.exists(path)
