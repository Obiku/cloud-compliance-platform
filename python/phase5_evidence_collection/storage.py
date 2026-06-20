"""Writes evidence snapshots to S3, organised by control ID and timestamp:
evidence/<control_id>/<YYYY>/<MM>/<DD>/<HHMMSS>/snapshot.json
"""

from __future__ import annotations

import datetime
import json


def evidence_key(control_id: str, generated_at: datetime.datetime, filename: str = "snapshot.json") -> str:
    timestamp_path = generated_at.strftime("%Y/%m/%d/%H%M%S")
    return f"evidence/{control_id}/{timestamp_path}/{filename}"


def write_evidence(
    s3, bucket: str, control_id: str, snapshot: dict, generated_at: datetime.datetime
) -> str:
    key = evidence_key(control_id, generated_at)
    body = json.dumps(
        {"control_id": control_id, "generated_at": generated_at.isoformat(), **snapshot},
        indent=2,
        default=str,
    )
    s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"))
    return key
