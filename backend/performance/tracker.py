"""
PrivyBrowse AI — Lightweight Performance & Telemetry Tracker
Collects real latency measurements across pipeline stages and computes statistical
distributions (Average, Median, P95, Min, Max, Samples) without artificial fabrication.
"""

import time
import os
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.performance.schemas import LatencyStats, StageMetric


class PerformanceTracker:
    """
    Centralized lightweight performance measurement engine.
    """

    def __init__(self, max_samples_per_stage: int = 500):
        self.max_samples = max_samples_per_stage
        self._samples: Dict[str, List[float]] = {
            "PREPROCESSING": [],
            "OPENCV_DETECTION": [],
            "OCR_EXTRACTION": [],
            "CONTEXT_FUSION": [],
            "TOTAL_PERCEPTION": [],
            "PII_DETECTION": [],
            "LOCAL_REDACTION": [],
            "TOTAL_PRIVACY_GATE": [],
            "AGENT_PLANNING": [],
            "ACTION_VALIDATION": [],
            "ACTION_EXECUTION": [],
            "OUTCOME_VERIFICATION": [],
            "COMPLETE_AGENT_CYCLE": []
        }
        self._active_timers: Dict[str, float] = {}

    def start_timer(self, stage: str):
        """Starts high-resolution performance counter for a stage."""
        self._active_timers[stage] = time.perf_counter()

    def stop_timer(self, stage: str) -> float:
        """Stops timer, records duration in ms, and returns elapsed time."""
        t_start = self._active_timers.pop(stage, None)
        if t_start is None:
            return 0.0
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        self.record_sample(stage, elapsed_ms)
        return round(elapsed_ms, 2)

    def record_sample(self, stage: str, duration_ms: float):
        """Records a raw latency sample in ms."""
        if stage not in self._samples:
            self._samples[stage] = []
        self._samples[stage].append(duration_ms)
        if len(self._samples[stage]) > self.max_samples:
            self._samples[stage].pop(0)

    def get_stats(self, stage: str) -> LatencyStats:
        """Computes real statistical distribution for a given stage."""
        samples = self._samples.get(stage, [])
        if not samples:
            return LatencyStats()

        s_arr = np.array(samples)
        return LatencyStats(
            count=len(samples),
            avg_ms=round(float(np.mean(s_arr)), 2),
            median_ms=round(float(np.median(s_arr)), 2),
            p95_ms=round(float(np.percentile(s_arr, 95)), 2),
            min_ms=round(float(np.min(s_arr)), 2),
            max_ms=round(float(np.max(s_arr)), 2),
            samples=[round(x, 2) for x in samples[-20:]]  # Latest 20 samples
        )

    def get_all_distributions(self) -> Dict[str, LatencyStats]:
        """Returns statistical distributions for all tracked stages."""
        return {stage: self.get_stats(stage) for stage in self._samples}

    def get_memory_usage_mb(self) -> float:
        """Measures current process resident set size (RSS) memory in MB."""
        try:
            import resource
            # ru_maxrss in kilobytes on Linux, bytes on macOS
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On macOS ru_maxrss is in bytes; on Linux in KB
            import platform
            if platform.system() == "Darwin":
                return round(usage / (1024.0 * 1024.0), 2)
            else:
                return round(usage / 1024.0, 2)
        except Exception:
            return 0.0

    def clear(self):
        """Resets all collected samples and active timers."""
        for stage in self._samples:
            self._samples[stage].clear()
        self._active_timers.clear()
