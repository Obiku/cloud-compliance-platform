import datetime
from unittest.mock import MagicMock

from phase8_grc_metrics.publisher import NAMESPACE, publish_metrics


def test_publish_metrics_builds_one_data_point_per_metric_and_severity():
    cloudwatch = MagicMock()
    timestamp = datetime.datetime(2026, 6, 24, tzinfo=datetime.timezone.utc)

    publish_metrics(
        cloudwatch,
        config_non_compliant_count=102,
        security_hub_failed_count=226,
        guardduty_counts_by_severity={"Low": 1, "Medium": 0, "High": 2},
        cloudtrail_event_count=50,
        timestamp=timestamp,
    )

    cloudwatch.put_metric_data.assert_called_once()
    call_kwargs = cloudwatch.put_metric_data.call_args.kwargs
    assert call_kwargs["Namespace"] == NAMESPACE
    data = call_kwargs["MetricData"]

    by_name = {(d["MetricName"], d.get("Dimensions", [{}])[0].get("Value")): d["Value"] for d in data}
    assert by_name[("ConfigNonCompliantCount", None)] == 102
    assert by_name[("SecurityHubFailedFindingsCount", None)] == 226
    assert by_name[("CloudTrailEventVolume", None)] == 50
    assert by_name[("GuardDutyFindingsBySeverity", "Low")] == 1
    assert by_name[("GuardDutyFindingsBySeverity", "Medium")] == 0
    assert by_name[("GuardDutyFindingsBySeverity", "High")] == 2
    assert len(data) == 6
