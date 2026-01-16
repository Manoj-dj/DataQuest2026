"""
Risk scoring engine for disaster events.
Calculates real-time risk scores based on severity, population impact,
disaster type, and other contextual factors.
"""

import numpy as np
from typing import Dict
from src.utils.schemas import SeverityLevel, DisasterType

class RiskScoringEngine:
    def __init__(self, config: Dict):
        self.severity_weights = config.get('severity_weights', {
            'Red': 10,
            'Orange': 7,
            'Green': 3,
            'Unknown': 5
        })
        
        self.disaster_multipliers = config.get('disaster_type_multipliers', {
            'earthquake': 1.2,
            'tsunami': 1.5,
            'wildfire': 1.1,
            'flood': 1.0,
            'cyclone': 1.3,
            'volcano': 1.4,
            'drought': 0.8,
            'unknown': 1.0
        })
    
    def calculate_risk_score(
        self,
        severity: str,
        population_affected: int,
        disaster_type: str,
        magnitude: float = None
    ) -> float:
        """
        Calculate comprehensive risk score (0-10 scale).
        
        Formula: base_score × (1 + pop_factor) × type_multiplier × magnitude_factor
        """
        base_score = self.severity_weights.get(severity, 5)
        
        pop_factor = self._calculate_population_factor(population_affected)
        
        type_multiplier = self.disaster_multipliers.get(disaster_type, 1.0)
        
        magnitude_factor = self._calculate_magnitude_factor(magnitude, disaster_type)
        
        risk_score = base_score * (1 + pop_factor) * type_multiplier * magnitude_factor
        
        return min(max(risk_score, 0.0), 10.0)
    
    def _calculate_population_factor(self, population: int) -> float:
        """
        Logarithmic scaling for population impact.
        """
        if population <= 0:
            return 0.0
        
        log_pop = np.log10(max(population, 1))
        normalized = log_pop / 6.0
        
        return min(normalized, 1.0)
    
    def _calculate_magnitude_factor(self, magnitude: float, disaster_type: str) -> float:
        """
        Adjust risk based on disaster magnitude (earthquakes, etc.).
        """
        if magnitude is None:
            return 1.0
        
        if disaster_type == 'earthquake':
            if magnitude >= 7.0:
                return 1.5
            elif magnitude >= 6.0:
                return 1.3
            elif magnitude >= 5.0:
                return 1.1
            else:
                return 0.9
        
        return 1.0
    
    def explain_risk_score(
        self,
        severity: str,
        population_affected: int,
        disaster_type: str,
        magnitude: float,
        final_score: float
    ) -> Dict[str, float]:
        """
        Provide explainable breakdown of risk score components.
        """
        base_score = self.severity_weights.get(severity, 5)
        pop_factor = self._calculate_population_factor(population_affected)
        type_mult = self.disaster_multipliers.get(disaster_type, 1.0)
        mag_factor = self._calculate_magnitude_factor(magnitude, disaster_type)
        
        return {
            'final_score': round(final_score, 2),
            'severity_contribution': round(base_score, 2),
            'population_impact': round(base_score * pop_factor, 2),
            'disaster_type_factor': round(type_mult, 2),
            'magnitude_factor': round(mag_factor, 2),
            'explanation': self._generate_explanation(
                severity, population_affected, disaster_type, magnitude
            )
        }
    
    def _generate_explanation(
        self,
        severity: str,
        population: int,
        disaster_type: str,
        magnitude: float
    ) -> str:
        """
        Generate human-readable risk explanation.
        """
        parts = []
        
        parts.append(f"Severity level: {severity}")
        
        if population > 10000:
            parts.append(f"High population impact: {population:,} people affected")
        elif population > 1000:
            parts.append(f"Moderate population impact: {population:,} people affected")
        
        if magnitude and magnitude >= 6.0:
            parts.append(f"High magnitude event: {magnitude}")
        
        parts.append(f"Disaster type: {disaster_type}")
        
        return " | ".join(parts)
