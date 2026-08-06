from dataclasses import dataclass

@dataclass
class DecisionPolicy:
    """
    Business configuration governing the Decision Intelligence layer.
    Allows business stakeholders to change deployment behavior without changing mathematical logic.
    """
    # Risk Tolerance
    min_confidence_to_switch: str = "Medium" # Baseline must be retained if confidence is below this
    
    # Deployment ROI Thresholds
    regional_min_improvement_abs: float = 0.010   # 1.0% WAPE improvement required over Global
    segmented_min_improvement_abs: float = 0.020  # 2.0% WAPE improvement required over Regional
    global_dominance_ratio: float = 0.50          # Global model wins if >50% of segments select it
    
    # Operational Complexity Limits
    max_models_low_complexity: int = 1
    max_models_medium_complexity: int = 4
    
    # Business Impact Classification Thresholds
    impact_high_abs: float = 0.03   # 3.0% WAPE absolute improvement
    impact_high_rel: float = 0.20   # 20% relative improvement
    impact_med_abs: float = 0.01    # 1.0% WAPE absolute improvement
    impact_med_rel: float = 0.05    # 5% relative improvement
