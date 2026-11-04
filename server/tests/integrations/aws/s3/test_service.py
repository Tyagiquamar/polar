from unittest.mock import MagicMock

import pytest
from botocore.client import ClientError

from polar.integrations.aws.s3.exceptions import S3FileError
from polar.integrations.aws.s3.schemas import (
    S3FileUploadCompleted,
    S3FileUploadCompletedPart,
)
from polar.integrations.aws.s3.service import S3Service


class TestGetObjectOrRaise:
    def test_omits_empty_version_id(self) -> None:
        client = MagicMock()
        client.get_object.return_value = {"Body": b"pdf"}

        result = S3Service(bucket="bucket", client=client).get_object_or_raise(
            "support_case_attachment/file.pdf"
        )

        assert result == {"Body": b"pdf"}
        client.get_object.assert_called_once_with(
            Bucket="bucket",
            Key="support_case_attachment/file.pdf",
            ChecksumMode="ENABLED",
        )

    def test_passes_version_id(self) -> None:
        client = MagicMock()
        client.get_object.return_value = {"Body": b"pdf"}

        S3Service(bucket="bucket", client=client).get_object_or_raise(
            "path/file.pdf", s3_version_id="v1"
        )

        client.get_object.assert_called_once_with(
            Bucket="bucket",
            Key="path/file.pdf",
            VersionId="v1",
            ChecksumMode="ENABLED",
        )

    def test_preserves_s3_error(self) -> None:
        client = MagicMock()
        error = ClientError(
            {
                "Error": {
                    "Code": "InvalidArgument",
                    "Message": "Invalid version id specified",
                }
            },
            "GetObject",
        )
        client.get_object.side_effect = error

        with pytest.raises(S3FileError) as exc_info:
            S3Service(bucket="bucket", client=client).get_object_or_raise(
                "path/file.pdf"
            )

        assert exc_info.value.__cause__ is error


class TestCompleteMultipartUpload:
    def test_client_error_becomes_structured_400(self) -> None:
        client = MagicMock()
        error = ClientError(
            {
                "Error": {
                    "Code": "NoSuchUpload",
                    "Message": "The specified upload does not exist.",
                }
            },
            "CompleteMultipartUpload",
        )
        client.complete_multipart_upload.side_effect = error
        completed = S3FileUploadCompleted(
            id="file-uuid-used-by-mistake",
            path="path/to/file",
            parts=[
                S3FileUploadCompletedPart(
                    number=1,
                    checksum_etag='"abc123"',
                    checksum_sha256_base64=None,
                )
            ],
        )

        with pytest.raises(S3FileError) as exc_info:
            S3Service(bucket="bucket", client=client).complete_multipart_upload(
                completed
            )

        assert exc_info.value.status_code == 400
        assert "upload.id" in exc_info.value.message
        assert exc_info.value.__cause__ is error
        client.head_object.assert_not_called()


class TestGetHeadOrRaise:
    def test_omits_empty_version_id(self) -> None:
        client = MagicMock()
        client.head_object.return_value = {"ETag": "etag"}

        result = S3Service(bucket="bucket", client=client).get_head_or_raise(
            "path/file.pdf"
        )

        assert result == {"ETag": "etag"}
        client.head_object.assert_called_once_with(Bucket="bucket", Key="path/file.pdf")

    def test_passes_version_id(self) -> None:
        client = MagicMock()
        client.head_object.return_value = {"ETag": "etag"}

        S3Service(bucket="bucket", client=client).get_head_or_raise(
            "path/file.pdf", s3_version_id="v1"
        )

        client.head_object.assert_called_once_with(
            Bucket="bucket", Key="path/file.pdf", VersionId="v1"
        )
