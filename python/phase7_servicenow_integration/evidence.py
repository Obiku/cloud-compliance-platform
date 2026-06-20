"""Reads the most recent evidence snapshot Phase 5 wrote for a control, from
evidence/<control_id>/<YYYY>/<MM>/<DD>/<HHMMSS>/snapshot.json (see
phase5_evidence_collection/storage.py for the writer side). Read-only - this
module never writes to the evidence bucket.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LatestEvidence:
    key: str
    s3_uri: str
    snapshot: dict[str, Any]


def get_latest_evidence(s3, bucket: str, control_id: str) -> LatestEvidence:
    prefix = f"evidence/{control_id}/"
    keys: list[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    if not keys:
        raise LookupError(f"No evidence found under s3://{bucket}/{prefix}")

    # Timestamp path segments are zero-padded, so lexicographic max == latest.
    latest_key = max(keys)
    body = s3.get_object(Bucket=bucket, Key=latest_key)["Body"].read()
    return LatestEvidence(
        key=latest_key,
        s3_uri=f"s3://{bucket}/{latest_key}",
        snapshot=json.loads(body),
    )
