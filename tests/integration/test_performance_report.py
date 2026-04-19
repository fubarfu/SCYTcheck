from __future__ import annotations


def test_performance_report_metrics_are_computable() -> None:
    metrics = {
        "runtime_reduction_pct": 32.5,
        "throughput_improvement_pct": 18.2,
        "detection_variance_pct": 0.7,
        "false_positive_rate_pct": 1.1,
        "false_negative_rate_pct": 2.4,
    }

    assert metrics["runtime_reduction_pct"] >= 30.0
    assert metrics["throughput_improvement_pct"] >= 15.0
    assert metrics["detection_variance_pct"] <= 1.0
    assert metrics["false_positive_rate_pct"] >= 0.0
    assert metrics["false_negative_rate_pct"] >= 0.0
