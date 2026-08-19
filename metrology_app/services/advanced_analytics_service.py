"""
Advanced Analytics Service for Premium Edition.

Provides enterprise-grade statistical analysis, machine learning capabilities,
and comprehensive measurement intelligence features for the $1000 premium edition.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from scipy import stats
from scipy.signal import savgol_filter
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import json

from ..db import list_calculations, get_calculation, DB_PATH
from metrology_core.context import to_decimal


class AdvancedAnalyticsEngine:
    """
    Enterprise-grade analytics engine with ML capabilities for 
    measurement intelligence, anomaly detection, and predictive maintenance.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self.scaler = StandardScaler()
        
    def load_historical_data(self, instrument_name: Optional[str] = None, 
                             limit: int = 1000) -> pd.DataFrame:
        """Load historical calibration data into pandas DataFrame for analysis."""
        calcs = list_calculations(record_class="CALIBRATION", limit=limit, db_path=self.db_path)
        
        if instrument_name:
            calcs = [c for c in calcs if c["instrument_name"] == instrument_name]
        
        records = []
        for calc in calcs:
            try:
                result_data = calc.get("result_data", {})
                decision_summary = result_data.get("decision_summary", {})
                uncertainty_summary = result_data.get("uncertainty_summary", {})
                
                record = {
                    "id": calc["id"],
                    "instrument_name": calc["instrument_name"],
                    "instrument_model": calc.get("instrument_model", ""),
                    "created_at": calc["created_at"],
                    "nominal_value": float(calc.get("nominal_value", 0)),
                    "tolerance_upper": float(calc.get("tolerance_upper", 0)),
                    "tolerance_lower": float(calc.get("tolerance_lower", 0)),
                    "error_of_indication": float(decision_summary.get("error_of_indication_mm", 0)),
                    "mean_measured": float(decision_summary.get("mean_measured_mm", 0)),
                    "expanded_uncertainty": float(uncertainty_summary.get("expanded_uncertainty_U95_mm", 0)),
                    "combined_uncertainty": float(uncertainty_summary.get("combined_standard_uncertainty_mm", 0)),
                    "tur": float(decision_summary.get("tur", 0)),
                    "verdict": calc.get("conformity_verdict", "UNKNOWN"),
                }
                records.append(record)
            except Exception as e:
                continue
                
        return pd.DataFrame(records)
    
    def compute_spcc_capability_indices(self, instrument_name: str) -> Dict[str, Any]:
        """
        Compute Statistical Process Control (SPC) capability indices:
        Cp, Cpk, Pp, Ppk for measurement process capability analysis.
        """
        df = self.load_historical_data(instrument_name)
        
        if df.empty or len(df) < 10:
            return {
                "instrument_name": instrument_name,
                "status": "INSUFFICIENT_DATA",
                "message": "Minimum 10 measurements required for SPC analysis"
            }
        
        # Extract measurement data
        measurements = df['error_of_indication'].values
        usl = df['tolerance_upper'].iloc[0]  # Upper Specification Limit
        lsl = df['tolerance_lower'].iloc[0]  # Lower Specification Limit
        
        # Calculate statistics
        mean = np.mean(measurements)
        std_dev = np.std(measurements, ddof=1)  # Sample standard deviation
        
        # Process Capability Indices (Cp, Cpk)
        if std_dev > 0:
            cp = (usl - lsl) / (6 * std_dev)
            cpu = (usl - mean) / (3 * std_dev)
            cpl = (mean - lsl) / (3 * std_dev)
            cpk = min(cpu, cpl)
        else:
            cp = cpk = cpu = cpl = float('inf')
        
        # Process Performance Indices (Pp, Ppk) - uses overall standard deviation
        overall_std = np.std(measurements, ddof=0)
        if overall_std > 0:
            pp = (usl - lsl) / (6 * overall_std)
            ppu = (usl - mean) / (3 * overall_std)
            ppl = (mean - lsl) / (3 * overall_std)
            ppk = min(ppu, ppl)
        else:
            pp = ppk = ppu = ppl = float('inf')
        
        # Determine capability status
        if cpk >= 1.33:
            capability_status = "EXCELLENT"
        elif cpk >= 1.0:
            capability_status = "CAPABLE"
        elif cpk >= 0.67:
            capability_status = "MARGINAL"
        else:
            capability_status = "INCABLE"
        
        return {
            "instrument_name": instrument_name,
            "sample_size": len(measurements),
            "mean_error": round(float(mean), 6),
            "std_deviation": round(float(std_dev), 6),
            "specification_limits": {
                "upper": round(float(usl), 6),
                "lower": round(float(lsl), 6)
            },
            "process_capability": {
                "cp": round(float(cp), 3),
                "cpk": round(float(cpk), 3),
                "cpu": round(float(cpu), 3),
                "cpl": round(float(cpl), 3)
            },
            "process_performance": {
                "pp": round(float(pp), 3),
                "ppk": round(float(ppk), 3),
                "ppu": round(float(ppu), 3),
                "ppl": round(float(ppl), 3)
            },
            "capability_status": capability_status,
            "interpretation": self._interpret_capability_indices(cp, cpk, pp, ppk),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _interpret_capability_indices(self, cp: float, cpk: float, pp: float, ppk: float) -> str:
        """Generate plain-language interpretation of capability indices."""
        if cpk >= 1.33:
            base = "Process is highly capable with excellent capability to meet specifications."
        elif cpk >= 1.0:
            base = "Process is capable with good ability to meet specifications."
        elif cpk >= 0.67:
            base = "Process is marginally capable - monitoring and improvement recommended."
        else:
            base = "Process is incapable - immediate corrective action required."
        
        comparison = f"Cp ({cp:.2f}) vs Cpk ({cpk:.2f}) indicates "
        if abs(cp - cpk) < 0.1:
            comparison += "process is well-centered."
        elif cpk < cp:
            comparison += "process is off-center - shift mean toward target."
        else:
            comparison += "unusual relationship between indices."
        
        return f"{base} {comparison}"
    
    def detect_anomalies_ml(self, instrument_name: str, 
                           contamination: float = 0.1) -> Dict[str, Any]:
        """
        Use machine learning (Isolation Forest) to detect anomalous measurements
        and calibration results that deviate from expected patterns.
        """
        df = self.load_historical_data(instrument_name)
        
        if df.empty or len(df) < 20:
            return {
                "instrument_name": instrument_name,
                "status": "INSUFFICIENT_DATA",
                "message": "Minimum 20 measurements required for ML anomaly detection"
            }
        
        # Prepare features for ML
        features = df[['error_of_indication', 'expanded_uncertainty', 
                      'combined_uncertainty', 'tur']].values
        
        # Handle NaN values
        features = np.nan_to_num(features, nan=0.0)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        anomalies = iso_forest.fit_predict(features_scaled)
        
        # Identify anomalies
        anomaly_indices = np.where(anomalies == -1)[0]
        anomaly_records = df.iloc[anomaly_indices].to_dict('records')
        
        # Calculate anomaly scores
        anomaly_scores = iso_forest.score_samples(features_scaled)
        
        return {
            "instrument_name": instrument_name,
            "total_measurements": len(df),
            "anomaly_count": len(anomaly_indices),
            "anomaly_percentage": round(len(anomaly_indices) / len(df) * 100, 2),
            "anomalies_detected": [
                {
                    "id": record["id"],
                    "date": record["created_at"],
                    "error_of_indication": record["error_of_indication"],
                    "expanded_uncertainty": record["expanded_uncertainty"],
                    "anomaly_score": float(anomaly_scores[idx]),
                    "reason": self._classify_anomaly(record, df)
                }
                for idx, record in zip(anomaly_indices, anomaly_records)
            ],
            "ml_model": "IsolationForest",
            "contamination_rate": contamination,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _classify_anomaly(self, record: Dict, df: pd.DataFrame) -> str:
        """Classify the likely reason for an anomaly."""
        error = record['error_of_indication']
        uncertainty = record['expanded_uncertainty']
        
        # Compare with statistical norms
        error_mean = df['error_of_indication'].mean()
        error_std = df['error_of_indication'].std()
        uncertainty_mean = df['expanded_uncertainty'].mean()
        
        reasons = []
        
        if abs(error - error_mean) > 2 * error_std:
            reasons.append("Unusual error magnitude")
        if uncertainty > 1.5 * uncertainty_mean:
            reasons.append("Elevated uncertainty")
        if record['verdict'] in ['FAIL', 'GUARD_BAND']:
            reasons.append("Conformity issue")
        
        return ", ".join(reasons) if reasons else "Statistical outlier"
    
    def perform_trend_analysis(self, instrument_name: str, 
                              forecast_periods: int = 6) -> Dict[str, Any]:
        """
        Perform advanced trend analysis including drift modeling, 
        seasonal patterns, and uncertainty growth projections.
        """
        df = self.load_historical_data(instrument_name)
        
        if df.empty or len(df) < 5:
            return {
                "instrument_name": instrument_name,
                "status": "INSUFFICIENT_DATA",
                "message": "Minimum 5 measurements required for trend analysis"
            }
        
        # Sort by date
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at')
        
        # Extract time series
        dates = df['created_at'].values
        errors = df['error_of_indication'].values
        uncertainties = df['expanded_uncertainty'].values
        
        # Calculate time deltas in days
        time_deltas = (dates - dates[0]).astype('timedelta64[D]').astype(float)
        
        # Linear regression for drift trend
        if len(time_deltas) > 1:
            error_slope, error_intercept, error_r, error_p, error_std = stats.linregress(time_deltas, errors)
            unc_slope, unc_intercept, unc_r, unc_p, unc_std = stats.linregress(time_deltas, uncertainties)
        else:
            error_slope = error_intercept = error_r = error_p = 0
            unc_slope = unc_intercept = unc_r = unc_p = 0
        
        # Smooth the data using Savitzky-Golay filter
        if len(errors) >= 5:
            window_size = min(5, len(errors) if len(errors) % 2 == 1 else len(errors) - 1)
            smoothed_errors = savgol_filter(errors, window_size, 2)
        else:
            smoothed_errors = errors
        
        # Forecast future values
        last_date = dates[-1]
        forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, forecast_periods + 1)]
        forecast_time_deltas = [(d - dates[0]).astype('timedelta64[D]').astype(float) for d in forecast_dates]
        
        forecast_errors = [error_intercept + error_slope * t for t in forecast_time_deltas]
        forecast_uncertainties = [unc_intercept + unc_slope * t for t in forecast_time_deltas]
        
        # Calculate trend strength
        error_trend_strength = abs(error_r) if abs(error_r) > 0.3 else 0
        unc_trend_strength = abs(unc_r) if abs(unc_r) > 0.3 else 0
        
        return {
            "instrument_name": instrument_name,
            "analysis_period": {
                "start": dates[0].isoformat(),
                "end": dates[-1].isoformat(),
                "days": int(time_deltas[-1])
            },
            "drift_analysis": {
                "slope_per_day": round(float(error_slope), 8),
                "slope_per_year": round(float(error_slope * 365), 6),
                "intercept": round(float(error_intercept), 6),
                "r_squared": round(float(error_r ** 2), 3),
                "p_value": round(float(error_p), 4),
                "trend_significance": "SIGNIFICANT" if error_p < 0.05 else "NOT_SIGNIFICANT",
                "trend_direction": "INCREASING" if error_slope > 0 else "DECREASING" if error_slope < 0 else "STABLE"
            },
            "uncertainty_growth": {
                "slope_per_day": round(float(unc_slope), 8),
                "slope_per_year": round(float(unc_slope * 365), 6),
                "intercept": round(float(unc_intercept), 6),
                "r_squared": round(float(unc_r ** 2), 3),
                "trend_significance": "SIGNIFICANT" if unc_p < 0.05 else "NOT_SIGNIFICANT"
            },
            "forecast": {
                "periods": forecast_periods,
                "projected_errors": [round(float(e), 6) for e in forecast_errors],
                "projected_uncertainties": [round(float(u), 6) for u in forecast_uncertainties],
                "forecast_dates": [d.isoformat() for d in forecast_dates]
            },
            "smoothed_data": [round(float(e), 6) for e in smoothed_errors],
            "trend_strength": {
                "error_trend": round(float(error_trend_strength), 2),
                "uncertainty_trend": round(float(unc_trend_strength), 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def generate_control_charts(self, instrument_name: str) -> Dict[str, Any]:
        """
        Generate Statistical Process Control (SPC) control charts data:
        X-bar chart, R chart, and individual/moving range charts.
        """
        df = self.load_historical_data(instrument_name)
        
        if df.empty or len(df) < 10:
            return {
                "instrument_name": instrument_name,
                "status": "INSUFFICIENT_DATA",
                "message": "Minimum 10 measurements required for control chart generation"
            }
        
        # Extract measurement data
        measurements = df['error_of_indication'].values
        dates = pd.to_datetime(df['created_at']).values
        
        # Calculate control limits for individual chart
        mean = np.mean(measurements)
        std_dev = np.std(measurements, ddof=1)
        
        # Control limits (3-sigma)
        ucl = mean + 3 * std_dev  # Upper Control Limit
        lcl = mean - 3 * std_dev  # Lower Control Limit
        
        # Calculate moving ranges (between consecutive points)
        moving_ranges = np.abs(np.diff(measurements))
        mr_mean = np.mean(moving_ranges) if len(moving_ranges) > 0 else 0
        
        # MR chart limits
        mr_ucl = 3.267 * mr_mean  # Upper Control Limit for MR chart
        
        # Identify out-of-control points
        out_of_control_high = measurements > ucl
        out_of_control_low = measurements < lcl
        out_of_control = out_of_control_high | out_of_control_low
        
        # Western Electric rules violations
        rule_violations = self._check_western_electric_rules(measurements, mean, std_dev)
        
        return {
            "instrument_name": instrument_name,
            "chart_type": "INDIVIDUAL_MOVING_RANGE",
            "individual_chart": {
                "data_points": [round(float(m), 6) for m in measurements],
                "dates": [d.isoformat() for d in dates],
                "center_line": round(float(mean), 6),
                "upper_control_limit": round(float(ucl), 6),
                "lower_control_limit": round(float(lcl), 6),
                "out_of_control_points": [int(i) for i, oc in enumerate(out_of_control) if oc],
                "process_capability": round(float(std_dev), 6)
            },
            "moving_range_chart": {
                "data_points": [round(float(mr), 6) for mr in moving_ranges],
                "dates": [d.isoformat() for d in dates[1:]],
                "center_line": round(float(mr_mean), 6),
                "upper_control_limit": round(float(mr_ucl), 6),
                "lower_control_limit": 0.0
            },
            "western_electric_rules": rule_violations,
            "process_status": "OUT_OF_CONTROL" if np.any(out_of_control) else "IN_CONTROL",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _check_western_electric_rules(self, measurements: np.ndarray, 
                                     mean: float, std_dev: float) -> Dict[str, Any]:
        """Check Western Electric statistical process control rules."""
        violations = {
            "rule1_beyond_3sigma": [],  # Point beyond 3σ
            "rule2_beyond_2sigma": [],  # 2 of 3 consecutive points beyond 2σ
            "rule3_beyond_1sigma": [],  # 4 of 5 consecutive points beyond 1σ
            "rule4_trend": [],          # 6 consecutive points increasing/decreasing
            "rule5_alternating": []     # 14 consecutive points alternating up/down
        }
        
        # Rule 1: Any point beyond 3σ
        for i, m in enumerate(measurements):
            if abs(m - mean) > 3 * std_dev:
                violations["rule1_beyond_3sigma"].append(i)
        
        # Rule 2: 2 of 3 consecutive points beyond 2σ (same side)
        for i in range(len(measurements) - 2):
            subset = measurements[i:i+3]
            beyond_upper = sum(m > mean + 2*std_dev for m in subset)
            beyond_lower = sum(m < mean - 2*std_dev for m in subset)
            if beyond_upper >= 2 or beyond_lower >= 2:
                violations["rule2_beyond_2sigma"].extend([i, i+1, i+2])
        
        # Rule 3: 4 of 5 consecutive points beyond 1σ (same side)
        for i in range(len(measurements) - 4):
            subset = measurements[i:i+5]
            beyond_upper = sum(m > mean + 1*std_dev for m in subset)
            beyond_lower = sum(m < mean - 1*std_dev for m in subset)
            if beyond_upper >= 4 or beyond_lower >= 4:
                violations["rule3_beyond_1sigma"].extend([i, i+1, i+2, i+3, i+4])
        
        # Rule 4: 6 consecutive points increasing or decreasing
        for i in range(len(measurements) - 5):
            subset = measurements[i:i+6]
            if all(subset[j] < subset[j+1] for j in range(5)):
                violations["rule4_trend"].extend([i, i+1, i+2, i+3, i+4, i+5])
            elif all(subset[j] > subset[j+1] for j in range(5)):
                violations["rule4_trend"].extend([i, i+1, i+2, i+3, i+4, i+5])
        
        # Rule 5: 14 consecutive points alternating up/down
        for i in range(len(measurements) - 13):
            subset = measurements[i:i+14]
            alternating = True
            for j in range(13):
                if (subset[j] < subset[j+1] and subset[j+1] < subset[j+2]) or \
                   (subset[j] > subset[j+1] and subset[j+1] > subset[j+2]):
                    alternating = False
                    break
            if alternating:
                violations["rule5_alternating"].extend([i + k for k in range(14)])
        
        # Remove duplicates
        for key in violations:
            violations[key] = list(set(violations[key]))
        
        return violations
    
    def cluster_instruments(self, min_samples: int = 3) -> Dict[str, Any]:
        """
        Use DBSCAN clustering to group instruments with similar measurement behavior
        and uncertainty characteristics for fleet-level insights.
        """
        df = self.load_historical_data(limit=2000)
        
        if df.empty or len(df) < min_samples:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Minimum {min_samples} measurements required for clustering"
            }
        
        # Aggregate by instrument
        instrument_stats = df.groupby('instrument_name').agg({
            'error_of_indication': ['mean', 'std'],
            'expanded_uncertainty': 'mean',
            'tur': 'mean'
        }).reset_index()
        
        instrument_stats.columns = ['instrument_name', 'error_mean', 'error_std', 
                                   'uncertainty_mean', 'tur_mean']
        
        # Prepare features for clustering
        features = instrument_stats[['error_mean', 'error_std', 'uncertainty_mean', 'tur_mean']].values
        features = np.nan_to_num(features, nan=0.0)
        features_scaled = self.scaler.fit_transform(features)
        
        # Apply DBSCAN clustering
        clustering = DBSCAN(eps=0.5, min_samples=min_samples).fit(features_scaled)
        labels = clustering.labels_
        
        # Organize results by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:
                cluster_name = "NOISE"
            else:
                cluster_name = f"CLUSTER_{label}"
            
            if cluster_name not in clusters:
                clusters[cluster_name] = []
            
            clusters[cluster_name].append({
                "instrument_name": instrument_stats.iloc[idx]['instrument_name'],
                "error_mean": float(instrument_stats.iloc[idx]['error_mean']),
                "error_std": float(instrument_stats.iloc[idx]['error_std']),
                "uncertainty_mean": float(instrument_stats.iloc[idx]['uncertainty_mean']),
                "tur_mean": float(instrument_stats.iloc[idx]['tur_mean'])
            })
        
        return {
            "total_instruments": len(instrument_stats),
            "clusters_found": len([k for k in clusters.keys() if k != "NOISE"]),
            "noise_points": len(clusters.get("NOISE", [])),
            "clusters": {
                cluster_name: {
                    "count": len(instruments),
                    "characteristics": self._describe_cluster(instruments),
                    "instruments": instruments
                }
                for cluster_name, instruments in clusters.items()
            },
            "clustering_algorithm": "DBSCAN",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _describe_cluster(self, instruments: List[Dict]) -> Dict[str, Any]:
        """Generate statistical description of a cluster."""
        errors = [inst['error_mean'] for inst in instruments]
        uncertainties = [inst['uncertainty_mean'] for inst in instruments]
        
        return {
            "avg_error": round(np.mean(errors), 6),
            "avg_uncertainty": round(np.mean(uncertainties), 6),
            "error_range": [round(np.min(errors), 6), round(np.max(errors), 6)],
            "uncertainty_range": [round(np.min(uncertainties), 6), round(np.max(uncertainties), 6)]
        }


# Singleton instance for service layer
_analytics_engine = None

def get_analytics_engine(db_path: Optional[str] = None) -> AdvancedAnalyticsEngine:
    """Get or create the analytics engine singleton."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AdvancedAnalyticsEngine(db_path)
    return _analytics_engine

def compute_spcc_capability_indices(instrument_name: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Compute SPC capability indices for an instrument."""
    engine = get_analytics_engine(db_path)
    return engine.compute_spcc_capability_indices(instrument_name)

def detect_anomalies_ml(instrument_name: str, contamination: float = 0.1, 
                       db_path: Optional[str] = None) -> Dict[str, Any]:
    """Detect anomalies using machine learning."""
    engine = get_analytics_engine(db_path)
    return engine.detect_anomalies_ml(instrument_name, contamination)

def perform_trend_analysis(instrument_name: str, forecast_periods: int = 6,
                          db_path: Optional[str] = None) -> Dict[str, Any]:
    """Perform trend analysis and forecasting."""
    engine = get_analytics_engine(db_path)
    return engine.perform_trend_analysis(instrument_name, forecast_periods)

def generate_control_charts(instrument_name: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Generate SPC control charts."""
    engine = get_analytics_engine(db_path)
    return engine.generate_control_charts(instrument_name)

def cluster_instruments(min_samples: int = 3, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Cluster instruments by behavior patterns."""
    engine = get_analytics_engine(db_path)
    return engine.cluster_instruments(min_samples)