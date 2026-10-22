"""
Quantile Gradient-Boosted Flood Forecasting & Uncertainty Model.

Section 5.2 & 5.3:
- Feature-based model predicting water depth at future lead times.
- Quantile regression at q10, q50 (median forecast), and q90 (conservative bound).
- Calculates prediction interval coverage and width.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import joblib


class QuantileBoostedFloodForecaster:
    """
    Multi-quantile gradient-boosted surrogate model for flood depth forecasting.
    Trains three regressors:
    - q10: Lower 10th percentile bound
    - q50: Median point prediction
    - q90: Upper 90th percentile bound (used by risk-aware routing)
    """

    def __init__(self, random_state: int = 42):
        self.model_name = "QuantileHistGBM_Surrogate_v1.0"
        self.version = "1.0.0"
        self.random_state = random_state

        # Initialize quantile models
        self.model_q10 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.10,
            max_iter=100,
            learning_rate=0.08,
            random_state=random_state
        )
        self.model_q50 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.50,
            max_iter=100,
            learning_rate=0.08,
            random_state=random_state
        )
        self.model_q90 = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.90,
            max_iter=100,
            learning_rate=0.08,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Fits q10, q50, and q90 models on tabular feature matrix X and ground-truth depth y.
        Features in X:
        [
            current_depth_m,
            prev_depth_m,
            depth_delta_m,
            ground_elevation_m,
            slope_deg,
            flow_accumulation_m2,
            rainfall_intensity_mmh,
            future_rainfall_step_mmh,
            lead_time_minutes
        ]
        """
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)

        self.model_q10.fit(X, y)
        self.model_q50.fit(X, y)
        self.model_q90.fit(X, y)
        self.is_fitted = True

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Predicts depth distribution bounds for input features.
        Returns:
            - 'q10': lower bound
            - 'q50': median predicted depth
            - 'q90': upper conservative bound
            - 'interval_width': q90 - q10
            - 'inundation_prob': heuristic exceedance prob P(depth >= 0.30m)
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict.")

        X = np.asarray(X, dtype=np.float32)
        p10 = np.maximum(0.0, self.model_q10.predict(X))
        p50 = np.maximum(0.0, self.model_q50.predict(X))
        p90 = np.maximum(p50, self.model_q90.predict(X))  # Monotonicity enforcement

        interval_width = p90 - p10

        # Heuristic exceedance probability estimation using Gaussian tail fit from [q10, q90]
        # sigma approx (q90 - q10) / (2 * 1.28)
        sigma = np.maximum(1e-4, interval_width / 2.56)
        z = (0.30 - p50) / sigma
        # Approx standard normal CDF: 0.5 * (1 + erf(-z / sqrt(2)))
        from scipy.special import erf
        exceed_prob = 0.5 * (1.0 - erf(z / np.sqrt(2.0)))
        exceed_prob = np.clip(exceed_prob, 0.0, 1.0)

        return {
            "q10": p10,
            "q50": p50,
            "q90": p90,
            "interval_width": interval_width,
            "inundation_prob": exceed_prob
        }

    def evaluate_uncertainty(self, y_true: np.ndarray, preds: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Evaluates accuracy and uncertainty calibration:
        - Interval Coverage (nominal target: 80% for [q10, q90])
        - Mean Interval Width (meters)
        - MAE on median forecast (q50)
        - RMSE on median forecast (q50)
        """
        y_true = np.asarray(y_true, dtype=np.float32)
        q10 = preds["q10"]
        q50 = preds["q50"]
        q90 = preds["q90"]

        # Coverage: fraction of true values falling between q10 and q90
        in_interval = (y_true >= q10) & (y_true <= q90)
        coverage = float(np.mean(in_interval))
        mean_width = float(np.mean(q90 - q10))

        errors = q50 - y_true
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))

        return {
            "coverage_80pct_nominal": round(coverage, 4),
            "mean_interval_width_m": round(mean_width, 4),
            "median_mae_m": round(mae, 4),
            "median_rmse_m": round(rmse, 4)
        }
