"""Minimal ServiceNow Table API client. Credentials are read from environment
variables (SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD) - never hardcoded or logged.
"""

from __future__ import annotations

import os
from typing import Any

import requests


class ServiceNowClient:
    def __init__(self, instance: str | None = None, user: str | None = None, password: str | None = None):
        self.instance = instance or os.environ["SNOW_INSTANCE"]
        self._auth = (user or os.environ["SNOW_USER"], password or os.environ["SNOW_PASSWORD"])
        self._base = f"https://{self.instance}.service-now.com/api/now/table"

    def query(
        self, table: str, sysparm_query: str | None = None, fields: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"sysparm_limit": limit}
        if sysparm_query:
            params["sysparm_query"] = sysparm_query
        if fields:
            params["sysparm_fields"] = fields
        resp = requests.get(
            f"{self._base}/{table}", auth=self._auth, params=params,
            headers={"Accept": "application/json"}, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]

    def create(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(
            f"{self._base}/{table}", auth=self._auth, json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]

    def update(self, table: str, sys_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = requests.patch(
            f"{self._base}/{table}/{sys_id}", auth=self._auth, json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]
