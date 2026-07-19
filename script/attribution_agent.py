import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_recommendation(source_name):
    """Generate actionable recommendations for city administrators based on the source."""
    recs = {
        "Traffic": "Consider traffic management measures, reroute heavy vehicles, and enforce emission checks.",
        "Industry": "Inspect nearby industrial sources for emission compliance and stack height regulations.",
        "Construction": "Review dust suppression compliance (water sprinkling, covers) at nearby construction sites.",
        "Biomass": "Investigate active burning alerts and deploy field teams to prevent illegal burning.",
        "Regional Background": "Coordinate with state/regional authorities on broad emission reduction policies."
    }
    return recs.get(source_name, "")

def calculate_confidence(evidence_json):
    """
    Calculate overall system attribution confidence (0-1).
    Formula: Base (0.60) + Total Signal Strength (sum of raw scores * 0.15) +/- Context Modifiers.
    This ensures confidence scales smoothly with raw data strength rather than using rigid tiers.
    """
    raw = evidence_json.get('raw_scores', {})
    met = evidence_json.get('meteorology', {})
    
    # 1. Base confidence
    conf = 0.60
    
    # 2. Continuous scaling based on overall signal strength
    total_score = sum(raw.values())
    conf += min(0.30, total_score * 0.15)
    
    # 3. Wind reliability context
    wind_speed = met.get('wind_speed_kmh', 0)
    if wind_speed < 2:
        conf -= 0.10 # Stagnant wind makes source transport unpredictable
    elif wind_speed > 5:
        conf += 0.05
        
    # 4. Data availability context
    biomass_ev = evidence_json.get('evidence', {}).get('biomass', [])
    if any("unavailable" in str(e).lower() for e in biomass_ev):
        conf -= 0.10
        
    return max(0.1, min(0.97, round(conf, 3)))

def calculate_source_confidence(source_name, raw_score, evidence_list, wind_speed):
    """
    Calculate continuous source-specific confidence (0 to 1).
    Formula: Base (0.50) + Evidence Strength (raw_score * 0.30) + Observations (count * 0.05) +/- Context Modifiers.
    This continuous scaling prevents values from clustering artificially at round numbers.
    """
    # 1. Base Confidence
    conf = 0.50
    
    # 2. Continuous scaling based on raw evidence strength (max +0.30)
    conf += min(0.30, raw_score * 0.30)
    
    # 3. Number of supporting observations (+0.05 per observation)
    conf += (len(evidence_list) * 0.05)
    
    # 4. Context Modifiers (Wind & Data availability)
    ev_str = " ".join(evidence_list).lower()
    
    if source_name in ["Industry", "Construction", "Biomass", "Regional Background"]:
        # Wind speeds < 2 km/h reduce confidence by 0.10, > 10 km/h increase by 0.10
        if wind_speed < 2.0:
            conf -= 0.10
        elif wind_speed > 10.0:
            conf += 0.10
            
    if source_name == "Biomass" and ("unavailable" in ev_str or "0 active fires" in ev_str):
        conf -= 0.30
        
    if source_name == "Traffic" and ("no2" in ev_str or "co" in ev_str):
        conf += 0.10 # Chemical signature validates the spatial data
        
    return max(0.1, min(0.97, round(conf, 3)))

def run_attribution_agent(predicted_pm25, evidence_json):
    """
    Main Attribution Engine.
    Converts raw geospatial scores into normalized percentages.
    """
    raw = evidence_json.get('raw_scores', {})
    
    # Map raw scores
    traffic_score = raw.get('traffic_score', 0)
    industry_score = raw.get('industrial_score', 0)
    construction_score = raw.get('construction_score', 0)
    biomass_score = raw.get('upwind_fire_score', 0)
    
    # Baseline regional background score. 
    background_score = 0.20
    
    total = traffic_score + industry_score + construction_score + biomass_score + background_score
    if total == 0:
        total = 1.0
        
    # Normalize to percentages
    percentages = {
        "Traffic": round((traffic_score / total) * 100, 1),
        "Industry": round((industry_score / total) * 100, 1),
        "Construction": round((construction_score / total) * 100, 1),
        "Biomass": round((biomass_score / total) * 100, 1),
        "Regional Background": round((background_score / total) * 100, 1)
    }
    
    raw_scores_map = {
        "Traffic": traffic_score,
        "Industry": industry_score,
        "Construction": construction_score,
        "Biomass": biomass_score,
        "Regional Background": background_score
    }
    
    # Determine primary source
    primary_source = max(percentages, key=percentages.get)
    overall_confidence = calculate_confidence(evidence_json)
    
    # Format evidence arrays
    evidence_text_map = {
        "Traffic": evidence_json.get("evidence", {}).get("traffic", []),
        "Industry": evidence_json.get("evidence", {}).get("industry", []),
        "Construction": evidence_json.get("evidence", {}).get("construction", []),
        "Biomass": evidence_json.get("evidence", {}).get("biomass", []),
        "Regional Background": ["Base atmospheric pollution level representing broader urban/regional accumulation."]
    }
    
    # Add meteorology context to background evidence
    met = evidence_json.get("meteorology", {})
    wind_speed = met.get("wind_speed_kmh", 0)
    if wind_speed > 15:
        evidence_text_map["Regional Background"].append(f"High wind speeds ({wind_speed} km/h) indicate strong long-range regional transport.")
    
    # Construct final sources list
    sources = []
    for name, pct in sorted(percentages.items(), key=lambda item: item[1], reverse=True):
        if pct > 0:
            source_conf = calculate_source_confidence(name, raw_scores_map[name], evidence_text_map[name], wind_speed)
            sources.append({
                "name": name,
                "contribution_percentage": pct,
                "evidence": evidence_text_map[name],
                "recommendation": generate_recommendation(name),
                "confidence": source_conf
            })
            
    final_json = {
        "predicted_pm25": predicted_pm25,
        "primary_source": primary_source,
        "confidence": overall_confidence,
        "sources": sources
    }
    
    return final_json

def validate_attribution():
    """Validate the pipeline using Sion and Kurla station outputs."""
    sion_evidence = {
      "timestamp": "2026-07-20T08:00:00",
      "station": "Sion, Mumbai - MPCB",
      "latitude": 19.047,
      "longitude": 72.8746,
      "meteorology": {
        "wind_direction": 270,
        "wind_speed_kmh": 15
      },
      "raw_scores": {
        "traffic_score": 1.0,
        "industrial_score": 0.232,
        "construction_score": 0.406,
        "upwind_fire_score": 0.0
      },
      "evidence": {
        "traffic": [
          "Road density within 5km is 1987.0 km.",
          "Nearest major road is 364 meters away.",
          "Pollutant signature (High NO2 and CO) strongly indicates heavy vehicular combustion."
        ],
        "industry": [
          "Upwind sector (W) contains 0.23 sq km of industrial land use."
        ],
        "construction": [
          "Upwind sector (W) contains 0.10 sq km of construction/brownfield.",
          "Pollutant signature (High PM10 vs PM2.5 ratio) strongly indicates coarse dust suspension."
        ],
        "biomass": [
          "Detected 0 active fires within 50km radius."
        ]
      }
    }
    
    kurla_evidence = {
      "timestamp": "2023-07-28 00:00:00",
      "station": "Kurla, Mumbai - MPCB",
      "latitude": 19.0728,
      "longitude": 72.8826,
      "meteorology": {
        "wind_direction": 270,
        "wind_speed_kmh": 17.7
      },
      "raw_scores": {
        "traffic_score": 0.99,
        "industrial_score": 0.91,
        "construction_score": 0.406,
        "upwind_fire_score": 0.0
      },
      "evidence": {
        "traffic": [
          "Road density within 5km is 2151.4 km.",
          "Nearest major road is 75 meters away."
        ],
        "industry": [
          "Upwind sector (N) contains 0.91 sq km of industrial land use."
        ],
        "construction": [
          "Upwind sector (N) contains 0.10 sq km of construction/brownfield.",
          "Pollutant signature (High PM10 vs PM2.5 ratio) strongly indicates coarse dust suspension."
        ],
        "biomass": [
          "Detected 0 active fires within 50km radius."
        ]
      }
    }
    
    print("\n--- ATTRIBUTION AGENT: SION TEST ---")
    print(json.dumps(run_attribution_agent(125.4, sion_evidence), indent=2))
    
    print("\n--- ATTRIBUTION AGENT: KURLA TEST ---")
    print(json.dumps(run_attribution_agent(125.4, kurla_evidence), indent=2))
    print("--------------------------------------\n")

if __name__ == "__main__":
    validate_attribution()
