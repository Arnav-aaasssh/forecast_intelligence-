from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class ScorerConfig:
    weights: dict = field(default_factory=lambda: {"WAPE": 0.35, "Hit10": 0.25, "Bias": 0.20, "Stability": 0.20})
    wape_bounds: tuple = (0.05, 0.40)
    bias_bounds: tuple = (0.00, 0.20)
    stab_bounds: tuple = (0.00, 0.30)
    hit10_bounds: tuple = (0.90, 0.30)
    hit_band: float = 0.10
    min_rows: int = 30
    min_wape_improvement: float = 0.015
    sig_alpha: float = 0.05
    baseline_model: str = "Manual"

@dataclass
class Anomaly:
    week: str
    z_score: float
    volume: float

@dataclass
class ActualsAnalysis:
    mean_volume: float
    volatility_cv: float
    trend: str
    anomalies: List[Anomaly]

@dataclass
class ComparisonEvidence:
    better_wape: bool
    better_bias: bool
    better_stability: bool
    is_tied: bool = False

@dataclass
class StatisticalEvidence:
    confidence_level: str
    p_value: float
    win_rate: float

@dataclass
class PerformanceEvidence:
    n_rows: int
    n_weeks: int
    wape: float
    abs_bias: float
    std_err_pct: float
    iqr_stability: float
    hit10: float
    composite_score: float
    status: str

@dataclass
class RecommendationEvidence:
    model_name: str
    is_top_scorer: bool
    is_statistical_winner: bool
    comparison: ComparisonEvidence
    statistics: StatisticalEvidence

@dataclass
class DegradationEvidence:
    model_name: str
    week_ending: str
    wape: float
    volatility: float
    anomaly_flag: bool
    z_score: float
    direction: str

@dataclass
class RecommendationResult:
    overall_winner: Optional[RecommendationEvidence]
    family_winners: Dict[str, RecommendationEvidence]
    region_winners: Dict[str, RecommendationEvidence]
    channel_winners: Dict[str, RecommendationEvidence]
    degradation_indicators: List[DegradationEvidence]

@dataclass
class BusinessImpact:
    baseline_wape: Optional[float]
    challenger_wape: float
    abs_improvement: Optional[float]
    rel_improvement: Optional[float]
    impact_rating: str  # High, Medium, Low
    is_greenfield: bool = False
    
@dataclass
class DeploymentScenario:
    name: str
    models_required: int
    complexity_rating: str # High, Medium, Low
    blended_wape: float
    selected: bool = False
    
@dataclass
class ExecutiveDecision:
    action: str  # Retain Incumbent, Pilot Deployment, Full Global Switch, Segmented Switch
    business_impact: BusinessImpact
    deployment_scenario: DeploymentScenario
    all_scenarios: List[DeploymentScenario]
    reasoning: str
