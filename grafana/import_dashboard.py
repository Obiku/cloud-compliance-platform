"""Imports grafana/dashboard.json into a live Amazon Managed Grafana workspace
via its HTTP API - dashboard-as-code instead of a manual UI import.

Usage:
    GRAFANA_ENDPOINT=https://g-xxxx.grafana-workspace.eu-west-2.amazonaws.com \
    GRAFANA_TOKEN=glsa_xxx \
    python grafana/import_dashboard.py

Both values come from Terraform outputs once `create_grafana_workspace = true`
has been applied: `terraform output -raw grafana_workspace_endpoint` and
`terraform output -raw grafana_dashboard_importer_token` (the token is short-
lived - 1 hour, set in terraform/modules/grafana/main.tf - re-apply to mint a
fresh one if it has expired).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

DASHBOARD_PATH = Path(__file__).parent / "dashboard.json"


def find_or_create_cloudwatch_datasource_uid(base_url: str, headers: dict) -> str:
    """The workspace's data_sources=["CLOUDWATCH"] setting only grants the IAM
    role permission to read CloudWatch - it does not create a Grafana
    datasource entry, confirmed by a real import attempt failing with "No
    CloudWatch datasource found" until this was added. authType "default"
    uses the workspace's own service-managed IAM role, no credentials needed.
    """
    resp = requests.get(f"{base_url}/api/datasources", headers=headers, timeout=30)
    resp.raise_for_status()
    for ds in resp.json():
        if ds["type"] == "cloudwatch":
            return ds["uid"]

    resp = requests.post(
        f"{base_url}/api/datasources",
        headers=headers,
        json={
            "name": "CloudWatch",
            "type": "cloudwatch",
            "access": "proxy",
            "jsonData": {"authType": "default", "defaultRegion": "eu-west-2"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["datasource"]["uid"]


def import_dashboard(base_url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    datasource_uid = find_or_create_cloudwatch_datasource_uid(base_url, headers)

    dashboard = json.loads(DASHBOARD_PATH.read_text())
    dashboard.pop("__inputs", None)
    raw = json.dumps(dashboard).replace("${DS_CLOUDWATCH}", datasource_uid)
    dashboard = json.loads(raw)

    resp = requests.post(
        f"{base_url}/api/dashboards/db",
        headers=headers,
        json={"dashboard": dashboard, "overwrite": True},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    endpoint = os.environ["GRAFANA_ENDPOINT"].rstrip("/")
    token = os.environ["GRAFANA_TOKEN"]
    result = import_dashboard(endpoint, token)
    print(json.dumps(result, indent=2))
    sys.exit(0)
