"""
metrics.py

Reusable, pure numerical functions for forecast performance metrics.
Uses NumPy for vectorized calculations. All functions are deterministic
and handle edge cases (zeros, empty inputs) safely.
"""

from __future__ import annotations
from typing import Union, Iterable

import logging
import numpy as np

# Minimal structured logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def safe_divide(
    numerator: Union[float, np.ndarray], 
    denominator: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Safely divide two numbers or arrays elementwise.
    Returns 0 where the denominator is zero (no division-by-zero error).
    """
    # Convert inputs to numpy arrays of type float
    num_arr = np.array(numerator, dtype=float)
    den_arr = np.array(denominator, dtype=float)
    result = np.zeros_like(num_arr, dtype=float)
    # Perform division where denom != 0
    np.divide(num_arr, den_arr, out=result, where=den_arr!=0)
    # Return scalar if inputs were scalar
    if result.shape == ():
        return float(result)
    return result


def calculate_error(
    forecast: Union[float, np.ndarray], 
    actual: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Forecast error (Forecast - Actual) for each item."""
    # Simple subtraction, vectorized by NumPy
    return np.array(forecast, dtype=float) - np.array(actual, dtype=float)


def calculate_absolute_error(
    forecast: Union[float, np.ndarray], 
    actual: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """Absolute forecast error |Forecast - Actual| for each item."""
    err = calculate_error(forecast, actual)
    return np.abs(err)


def calculate_accuracy(
    forecast: Union[float, np.ndarray], 
    actual: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """
    Forecast accuracy as a percentage: 
    `max(0, 1 - |Forecast - Actual| / |Actual|) * 100`.
    Returns 0% if Actual is zero to avoid division by zero.
    """
    f_arr = np.array(forecast, dtype=float)
    a_arr = np.array(actual, dtype=float)
    # Avoid divide-by-zero: mask where actual != 0
    result = np.zeros_like(f_arr, dtype=float)
    # Compute 1 - |error|/|actual|
    np.divide(np.abs(f_arr - a_arr), np.abs(a_arr), out=result, where=a_arr!=0)
    result = 1.0 - result
    # Clamp negatives to zero (no negative accuracy)
    result = np.maximum(result, 0.0)
    # Convert to percentage
    result *= 100.0
    # Ensure scalar return if appropriate
    if result.shape == ():
        return float(result)
    return result


def calculate_mae(
    errors: Iterable[float]
) -> float:
    """
    Mean Absolute Error (MAE): average of absolute errors.
    Args:
        errors: sequence of numeric error values.
    Returns:
        The mean of absolute values (float). Returns 0.0 for empty input.
    """
    arr = np.array(list(errors), dtype=float)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return 0.0
    # Use nan-mean to ignore NaN if present
    mae = np.nanmean(np.abs(arr))
    return float(mae) if not np.isnan(mae) else 0.0


def calculate_mape(
    forecasts: Iterable[float], 
    actuals: Iterable[float]
) -> float:
    """
    Mean Absolute Percentage Error (MAPE).
    Skips any terms where actual == 0.
    Returns percentage (0-100). Returns 0.0 if no valid terms.
    """
    f_arr = np.asarray(list(forecasts), dtype=float)
    a_arr = np.asarray(list(actuals), dtype=float)

    if f_arr.size == 0 or a_arr.size == 0:
        return 0.0

    mask = (
        ~np.isnan(f_arr)
        & ~np.isnan(a_arr)
        & (a_arr != 0)
    )

    if not np.any(mask):
        return 0.0

    percentage_errors = (
        np.abs(f_arr[mask] - a_arr[mask])
        / np.abs(a_arr[mask])
    )

    return float(np.mean(percentage_errors) * 100)


def calculate_bias(
    errors: Iterable[float]
) -> float:
    """
    Forecast bias (mean error): average of (Forecast - Actual).
    Positive means over-forecasting; negative means under-forecasting.
    Returns 0.0 for empty input.
    """
    arr = np.array(list(errors), dtype=float)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return 0.0
    bias_val = np.nanmean(arr)
    return float(bias_val) if not np.isnan(bias_val) else 0.0


def calculate_percentage_within_threshold(
    values: Iterable[Union[bool, float]], 
    threshold: float = 1.0
) -> float:
    """
    Percentage of values within ±threshold. If values are booleans, calculates the
    percent of True entries. If numeric, calculates percent where |v| <= threshold.
    Returns 0.0 for empty input.
    """
    arr = np.array(list(values))
    if arr.size == 0:
        return 0.0
    # If boolean, simply take mean of True=1, False=0
    if arr.dtype == bool:
        pct = np.mean(arr) * 100.0
        return float(pct)
    # Else treat as numeric values and apply threshold
    num_arr = np.array(arr, dtype=float)
    within = np.abs(num_arr) <= threshold
    pct = np.mean(within) * 100.0
    return float(pct)


def calculate_coefficient_of_variation(
    mean: float, 
    std: float
) -> float:
    """
    Coefficient of variation: std / mean.
    Returns 0.0 if mean==0 and std==0 (no variation), or inf if mean==0 and std>0.
    """
    # Handle zero mean explicitly to avoid division by zero
    if mean == 0.0:
        if std == 0.0:
            return 0.0
        else:
            return float("inf")
    return std / mean


def safe_mean(values: Iterable[float]) -> float:
    """
    Safe mean: returns the average of values, ignoring NaNs.
    Returns 0.0 if input is empty or all NaN.
    """
    arr = np.array(list(values), dtype=float)
    if arr.size == 0:
        return 0.0
    m = np.nanmean(arr)
    return float(m) if not np.isnan(m) else 0.0


def safe_std(values: Iterable[float]) -> float:
    """
    Safe standard deviation (population, ddof=0): ignores NaNs.
    Returns 0.0 if input has <2 values or all NaN.
    """
    arr = np.array(list(values), dtype=float)
    if arr.size < 2:
        return 0.0
    s = np.nanstd(arr)
    return float(s) if not np.isnan(s) else 0.0
