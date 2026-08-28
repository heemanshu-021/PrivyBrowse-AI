"""
PrivyBrowse AI — Performance Optimizations & Resource Management
Implements safe regex precompilation, model instance caching, and lightweight memory cleanup.
"""

import gc
import re
import cv2
from typing import Dict, Any, Optional


class PerformanceOptimizations:
    """
    Manages cached resources, precompiled patterns, and memory reclamation.
    """

    _cascade_cache: Dict[str, Any] = {}
    _regex_cache: Dict[str, Any] = {}

    @classmethod
    def get_haar_cascade(cls, cascade_name: str = "haarcascade_frontalface_default.xml") -> Optional[cv2.CascadeClassifier]:
        """Returns cached OpenCV Haar Cascade Classifier instance."""
        if cascade_name not in cls._cascade_cache:
            try:
                cascade_path = cv2.data.haarcascades + cascade_name
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    cls._cascade_cache[cascade_name] = cascade
                else:
                    cls._cascade_cache[cascade_name] = None
            except Exception:
                cls._cascade_cache[cascade_name] = None
        return cls._cascade_cache[cascade_name]

    @classmethod
    def get_compiled_regex(cls, pattern_str: str, flags: int = 0) -> re.Pattern:
        """Returns cached precompiled regular expression."""
        key = f"{pattern_str}_{flags}"
        if key not in cls._regex_cache:
            cls._regex_cache[key] = re.compile(pattern_str, flags)
        return cls._regex_cache[key]

    @classmethod
    def reclaim_memory(cls):
        """Explicitly reclaims unused memory buffers."""
        gc.collect()
