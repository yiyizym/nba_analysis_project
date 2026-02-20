"""
Uncertainty quantification module.

DEPRECATED: Calibration functionality has been moved to ml_framework.postprocessing.
This module now focuses on true uncertainty quantification methods.

For probability calibration, use:
    from ml_framework.postprocessing import ProbabilityCalibrator

For conformal prediction, use:
    from ml_framework.postprocessing import ConformalPredictor

This module is reserved for future uncertainty quantification methods such as:
    - Advanced Uncertainty estimation
    - Bayesian uncertainty quantification

Note: uncertainty_calibrator.py has been removed.
"""

import warnings

warnings.warn(
    "The ml_framework.uncertainty module is currently empty. "
    "Use ml_framework.postprocessing.ProbabilityCalibrator for calibration "
    "and ml_framework.postprocessing.ConformalPredictor for conformal prediction.",
    DeprecationWarning,
    stacklevel=2
)
