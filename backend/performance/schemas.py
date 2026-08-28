"""
PrivyBrowse AI — Performance & Benchmark Schemas
Data models for statistical latency distributions, benchmark stages,
accuracy metrics, and exportable benchmark reports.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LatencyStats(BaseModel):
    """Statistical distribution for a specific pipeline stage."""
    count: int = 0
    avg_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    samples: List[float] = Field(default_factory=list)


class StageMetric(BaseModel):
    stage: str
    duration_ms: float
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerceptionBenchmarkResult(BaseModel):
    page_name: str
    element_count: int
    interactive_count: int
    pii_count: int
    preprocess_ms: float
    detection_ms: float
    ocr_ms: float
    fusion_ms: float
    total_perception_ms: float
    avg_confidence: float


class PiiBenchmarkResult(BaseModel):
    dataset_name: str
    total_ground_truth_pii: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    detection_ms: float
    redaction_ms: float
    total_privacy_ms: float


class AgentTaskBenchmarkResult(BaseModel):
    task_id: str
    task_name: str
    completed: bool
    actions_executed: int
    retries: int
    planning_ms: float
    execution_ms: float
    verification_ms: float
    total_duration_ms: float
    recovery_succeeded: bool = True
    privacy_preserved: bool = True


class BenchmarkResults(BaseModel):
    """Complete system evaluation and benchmark report."""
    run_id: str
    timestamp: str
    environment: Dict[str, Any] = Field(default_factory=dict)
    
    # Aggregated Latency Distributions
    latency_distributions: Dict[str, LatencyStats] = Field(default_factory=dict)
    
    # Detailed Benchmark Runs
    perception_benchmarks: List[PerceptionBenchmarkResult] = Field(default_factory=list)
    pii_benchmarks: List[PiiBenchmarkResult] = Field(default_factory=list)
    agent_task_benchmarks: List[AgentTaskBenchmarkResult] = Field(default_factory=list)
    
    # Key Summary Rates (0.0 to 100.0%)
    task_success_rate_pct: float = 0.0
    action_success_rate_pct: float = 0.0
    verification_success_rate_pct: float = 0.0
    recovery_success_rate_pct: float = 0.0
    pii_precision_pct: float = 0.0
    pii_recall_pct: float = 0.0
    
    # Composite Evaluation Metric
    privybrowse_evaluation_score: float = 0.0
    
    # Resource Footprint
    baseline_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    total_benchmark_duration_ms: float = 0.0
