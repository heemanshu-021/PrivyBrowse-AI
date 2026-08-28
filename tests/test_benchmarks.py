"""
Automated Test Suite for Performance Profiling, Statistical Tracker, and Benchmark Runner
Tests:
  - PerformanceTracker sample accumulation & statistical distributions (Avg, Median, P95, Min, Max)
  - Perception Benchmark execution across 8 synthetic pages
  - PII Detection & Redaction Accuracy Benchmark (Precision, Recall, F1)
  - Agent Task Benchmark execution (10 standard tasks)
  - PrivyBrowse Evaluation Score calculation
  - Benchmark JSON export without sensitive data
  - Model & regex caching optimizations
"""

import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.performance.tracker import PerformanceTracker
from backend.performance.benchmarks import BenchmarkRunner
from backend.performance.optimizations import PerformanceOptimizations
from backend.performance.schemas import BenchmarkResults


def test_performance_tracker_statistics():
    print("[TEST 1] Testing PerformanceTracker Statistical Aggregation...")
    tracker = PerformanceTracker()

    tracker.start_timer("OCR_EXTRACTION")
    tracker.record_sample("OCR_EXTRACTION", 10.0)
    tracker.record_sample("OCR_EXTRACTION", 20.0)
    tracker.record_sample("OCR_EXTRACTION", 30.0)
    tracker.record_sample("OCR_EXTRACTION", 40.0)
    tracker.record_sample("OCR_EXTRACTION", 50.0)

    stats = tracker.get_stats("OCR_EXTRACTION")
    assert stats.count == 5
    assert stats.avg_ms == 30.0
    assert stats.median_ms == 30.0
    assert stats.min_ms == 10.0
    assert stats.max_ms == 50.0
    assert stats.p95_ms >= 45.0

    print("  ✓ Statistical distribution calculations (Avg, Median, P95, Min, Max) verified.")


def test_perception_benchmark_suite():
    print("\n[TEST 2] Testing Perception Benchmark Execution (8 Pages)...")
    runner = BenchmarkRunner()
    results = runner._run_perception_benchmarks(demo_dir="demo-pages")

    assert len(results) == 8
    for r in results:
        assert r.element_count > 0
        assert r.total_perception_ms > 0.0
        assert r.avg_confidence >= 0.30

    print(f"  ✓ Processed {len(results)} synthetic pages. Average latency: {sum(r.total_perception_ms for r in results)/len(results):.2f}ms.")


def test_pii_accuracy_and_latency_benchmark():
    print("\n[TEST 3] Testing PII Accuracy Benchmark (Precision, Recall, F1)...")
    runner = BenchmarkRunner()
    pii_results = runner._run_pii_benchmarks()

    assert len(pii_results) == 2
    for r in pii_results:
        assert r.true_positives > 0
        assert r.precision >= 0.90
        assert r.recall >= 0.85
        assert r.f1_score >= 0.85
        assert r.total_privacy_ms > 0.0

    print(f"  ✓ PII accuracy benchmark verified across Indian PAN/Aadhaar/Cards & Credentials (F1: {pii_results[0].f1_score}).")


def test_agent_task_benchmark_and_evaluation_score():
    print("\n[TEST 4] Testing Agent Task Benchmark & PrivyBrowse Evaluation Score...")
    runner = BenchmarkRunner()
    bench = runner.run_all_benchmarks()

    assert len(bench.agent_task_benchmarks) == 10
    assert bench.task_success_rate_pct >= 90.0
    assert bench.action_success_rate_pct >= 90.0
    assert bench.recovery_success_rate_pct >= 90.0
    assert bench.privybrowse_evaluation_score >= 85.0
    assert bench.total_benchmark_duration_ms > 0.0

    print(f"  ✓ 10 Agent Tasks evaluated. Task Success Rate: {bench.task_success_rate_pct}%, Evaluation Score: {bench.privybrowse_evaluation_score}%.")


def test_benchmark_export_zero_leak():
    print("\n[TEST 5] Testing Benchmark JSON Export & Privacy Invariant...")
    runner = BenchmarkRunner()
    bench = runner.run_all_benchmarks()

    export_path = "benchmark-results.json"
    abs_path = runner.export_results_json(bench, export_path)
    assert os.path.exists(abs_path)

    with open(abs_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Invariant assertions: No passwords, OTPs, raw screenshots in export
    data_str = json.dumps(data)
    assert "PrivySafePassword123!" not in data_str
    assert "data:image" not in data_str
    assert "593821" not in data_str

    print(f"  ✓ Export verified at '{export_path}'. 100% clean of sensitive values.")


def test_performance_optimizations_caching():
    print("\n[TEST 6] Testing Model & Regex Caching Optimizations...")
    # 1. Regex cache test
    p1 = PerformanceOptimizations.get_compiled_regex(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    p2 = PerformanceOptimizations.get_compiled_regex(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    assert p1 is p2, "Regex should be cached and reused"

    # 2. Haar Cascade cache test
    c1 = PerformanceOptimizations.get_haar_cascade()
    c2 = PerformanceOptimizations.get_haar_cascade()
    assert c1 is c2, "Haar Cascade instance should be cached and reused"

    # 3. Memory cleanup test
    PerformanceOptimizations.reclaim_memory()

    print("  ✓ Regex compilation and Haar Cascade caching optimizations verified.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING PERFORMANCE & BENCHMARK TEST SUITE")
    print("==================================================")
    test_performance_tracker_statistics()
    test_perception_benchmark_suite()
    test_pii_accuracy_and_latency_benchmark()
    test_agent_task_benchmark_and_evaluation_score()
    test_benchmark_export_zero_leak()
    test_performance_optimizations_caching()
    print("==================================================")
    print("ALL PERFORMANCE & BENCHMARK TESTS PASSED! ✓")
    print("==================================================")
