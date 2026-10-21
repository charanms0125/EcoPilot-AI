"""
Unit tests for the Green AI Efficiency Monitor.
Verifies execution time logging, cache hit tracking, avoided duplicate operations,
architecture pipeline comparison, and transparent empirical disclaimers.
"""

import time
import pytest
from src.green_ai import GreenAIMonitor


def test_green_ai_time_task_and_logging():
    """Verify time_task measures execution time accurately."""
    monitor = GreenAIMonitor()

    with monitor.time_task("Test Machine Learning Inference", "Scikit-Learn RF"):
        time.sleep(0.02)  # 20 ms

    summary = monitor.get_metrics_summary()
    assert summary["total_logged_tasks"] == 1
    assert summary["total_measured_execution_ms"] >= 15.0
    assert "Scikit-Learn RF" in summary["unique_models_active"]
    assert summary["cloud_api_calls_incurred"] == 0
    assert summary["is_zero_cost_local"] is True
    assert "GPU energy consumption and data-center carbon are not fabricated" in summary["disclaimer"]


def test_green_ai_cache_tracking():
    """Verify cache hits and avoided operations."""
    monitor = GreenAIMonitor()

    monitor.record_cache_hit("Forecast Cache Lookup", estimated_ms_avoided=300.0)
    monitor.record_cache_hit("Baseline Cache Lookup", estimated_ms_avoided=150.0)

    summary = monitor.get_metrics_summary()
    assert summary["cache_hits"] == 2
    assert summary["avoided_duplicate_operations"] == 2
    assert summary["cache_hit_ratio_pct"] == 100.0


def test_pipeline_comparison():
    """Verify comparative benchmark between local architecture and cloud LLM."""
    monitor = GreenAIMonitor()
    monitor.log_operation("RF Model Run", 250.0, "RandomForestRegressor")

    comp = monitor.get_pipeline_comparison()
    assert "ecopilot_local_architecture" in comp
    assert "unoptimized_cloud_llm_baseline" in comp
    assert comp["ecopilot_local_architecture"]["offline_functional"] is True
    assert comp["ecopilot_local_architecture"]["financial_api_cost_usd"] == "$0.00"
    assert "faster" in comp["comparison_metrics"]["latency_speedup"]
    assert len(comp["assumptions_disclosed"]) >= 2
