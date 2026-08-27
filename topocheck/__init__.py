"""topocheck — sanity checks for topology-aware segmentation claims.

Five checks, each of which caught a real result that looked publishable and
was not:

- :func:`random_repair_baseline` — does your repair beat a random one of equal size?
- :func:`decompose_errors`       — how much of the error is even repairable?
- :func:`tolerance_sweep`        — does the conclusion survive the metric's conventions?
- :func:`annotation_floor`       — is the improvement inside inter-annotator disagreement?
- :func:`prevalence_check`       — does a balanced-sample AUC survive the real class ratio?
"""
from .checks import (
    annotation_floor,
    decompose_errors,
    prevalence_check,
    random_repair_baseline,
    tolerance_sweep,
)
from .metrics import break_rate, false_merge_rate, label_with_tolerance
from .units import Unit, build_units, full_structure

__version__ = "0.1.0"
__all__ = [
    "Unit",
    "annotation_floor",
    "break_rate",
    "build_units",
    "decompose_errors",
    "false_merge_rate",
    "full_structure",
    "label_with_tolerance",
    "prevalence_check",
    "random_repair_baseline",
    "tolerance_sweep",
]
