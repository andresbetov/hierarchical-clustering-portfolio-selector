"""Out-of-sample validation layer (B6)."""

from .walk_forward import WalkForwardReport, walk_forward_evaluate

__all__ = ["WalkForwardReport", "walk_forward_evaluate"]
