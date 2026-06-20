import json

import boto3
import pytest
from moto import mock_aws

from phase7_servicenow_integration.evidence import get_latest_evidence


@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket="test-evidence-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield s3


def _put(s3, key, body):
    s3.put_object(Bucket="test-evidence-bucket", Key=key, Body=json.dumps(body).encode())


def test_get_latest_evidence_picks_most_recent_timestamp(s3_bucket):
    _put(s3_bucket, "evidence/CTRL-CONFIG-NISTCSF/2026/06/19/090000/snapshot.json", {"non_compliant_count": 5})
    _put(s3_bucket, "evidence/CTRL-CONFIG-NISTCSF/2026/06/20/090000/snapshot.json", {"non_compliant_count": 2})

    result = get_latest_evidence(s3_bucket, "test-evidence-bucket", "CTRL-CONFIG-NISTCSF")

    assert result.key == "evidence/CTRL-CONFIG-NISTCSF/2026/06/20/090000/snapshot.json"
    assert result.s3_uri == "s3://test-evidence-bucket/evidence/CTRL-CONFIG-NISTCSF/2026/06/20/090000/snapshot.json"
    assert result.snapshot == {"non_compliant_count": 2}


def test_get_latest_evidence_raises_when_no_evidence_exists(s3_bucket):
    with pytest.raises(LookupError):
        get_latest_evidence(s3_bucket, "test-evidence-bucket", "CTRL-NOT-COLLECTED")
