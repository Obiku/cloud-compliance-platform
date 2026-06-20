import datetime
import json

import boto3
import pytest
from moto import mock_aws

from phase5_evidence_collection.storage import evidence_key, write_evidence


def test_evidence_key_format():
    generated_at = datetime.datetime(2026, 6, 20, 14, 30, 5, tzinfo=datetime.timezone.utc)
    key = evidence_key("CTRL-CONFIG-NISTCSF", generated_at)
    assert key == "evidence/CTRL-CONFIG-NISTCSF/2026/06/20/143005/snapshot.json"


@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket="test-evidence-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield s3


def test_write_evidence_uploads_expected_key_and_body(s3_bucket):
    generated_at = datetime.datetime(2026, 6, 20, 14, 30, 5, tzinfo=datetime.timezone.utc)
    snapshot = {"overall_status": "NON_COMPLIANT", "non_compliant_count": 2}

    key = write_evidence(s3_bucket, "test-evidence-bucket", "CTRL-CONFIG-NISTCSF", snapshot, generated_at)

    assert key == "evidence/CTRL-CONFIG-NISTCSF/2026/06/20/143005/snapshot.json"
    body = s3_bucket.get_object(Bucket="test-evidence-bucket", Key=key)["Body"].read()
    parsed = json.loads(body)
    assert parsed["control_id"] == "CTRL-CONFIG-NISTCSF"
    assert parsed["non_compliant_count"] == 2
    assert parsed["generated_at"] == generated_at.isoformat()
