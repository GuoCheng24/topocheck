"""topocheck — sanity checks for topology-aware segmentation claims.

Five checks, each of which caught a real result that looked publishable and
was not:

- :func:`random_repair_baseline` — does your repair beat a random one of equal size?
- :func:`decompose_errors`       — how much of the error is even repairable?
- :func:`tolerance_sweep`        — does the conclusion survive the metric's conventions?
- :func:`annotation_floor`       — is the improvement inside inter-annotator disagreement?
- :func:`prevalence_check`       — does a balanced-sample AUC survive the real class ratio?
"""
from .units import Unit, build_units, full_structure
from .metrics import break_rate, label_with_tolerance
from .checks import (
    random_repair_baseline,
    decompose_errors,
    tolerance_sweep,
    annotation_floor,
    prevalence_check,
)

__version__ = "0.1.0"
__all__ = [
    "Unit", "build_units", "full_structure",
    "break_rate", "label_with_tolerance",
    "random_repair_baseline", "decompose_errors", "tolerance_sweep",
    "annotation_floor", "prevalence_check",
]
