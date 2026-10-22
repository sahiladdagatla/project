"""
Persistence Baseline for Flood Evolution Forecasting.

Section 5.2 requirement:
"Build baselines before complex models.
1. Persistence baseline: assumes water depth remains constant at the most recent observed value."
"""

import numpy as np
from typing import Dict, List, Any
from datetime import datetime


class PersistenceFloodModel:
    """
    Persistence model:
    Predicts that future water depth at lead time (t + h) equals the depth at observation time t:
        \\hat{d}_{t+h} = d_t
    """
    def __init__(self):
        self.model_name = "Persistence_Baseline_v1.0"
        self.version = "1.0.0"

    def predict(self, current_depths: np.ndarray, lead_steps: int = 1) -> np.ndarray:
        """
        Returns predicted depths across future lead times.
        Shape: (num_cells, lead_steps)
        """
        # Broadcast current depth across all requested lead steps
        current_depths = np.asarray(current_depths, dtype=np.float32)
        return np.repeat(current_depths[:, np.newaxis], lead_steps, axis=1)

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Computes standard hydrological error metrics:
        - MAE (Mean Absolute Error, meters)
        - RMSE (Root Mean Squared Error, meters)
        - Max Error (meters)
        """
        errors = y_pred - y_true
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        max_err = float(np.max(np.abs(errors)))
        return {
            "mae_m": round(mae, 4),
            "rmse_m": round(rmse, 4),
            "max_error_m": round(max_err, 4)
        }
