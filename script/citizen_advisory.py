import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# CPCB GROUND TRUTH LOOKUP TABLE
# ==========================================
CPCB_HEALTH_GUIDANCE = {
    "Good": "Minimal impact.",
    "Satisfactory": "Minor breathing discomfort to sensitive people.",
    "Moderate": "Breathing discomfort to the people with lungs, asthma and heart diseases.",
    "Poor": "Breathing discomfort to most people on prolonged exposure.",
    "Very Poor": "Respiratory illness on prolonged exposure.",
    "Severe": "Affects healthy people and seriously impacts those with existing diseases."
}

# ==========================================
# LLM PROMPT TEMPLATES
# ==========================================
SYSTEM_PROMPT = """You are a highly constrained natural language translation AI designed to deliver public health advisories regarding air quality in India.
You MUST follow these strict safety rules:
1. You are provided with an official, standardized public health guidance text from the Central Pollution Control Board (CPCB) of India.
2. Your ONLY job is to phrase this standardized guidance naturally and translate it into English, Hindi, and Marathi.
3. You MUST NOT invent, generate, or hallucinate any medical claims, dosages, or specific remedies (e.g., 'wear an N95 mask', 'take medication') beyond what is logically implied by the CPCB guidance text. You are not a medical professional.
4. You must generate two tone variants per language:
   - "general_public": A standard advisory based on the guidance.
   - "sensitive_groups": A more cautious framing of the SAME guidance specifically addressing the elderly, children, pregnant individuals, and those with respiratory/cardiac conditions.
5. Your output MUST be raw valid JSON ONLY, with no markdown formatting (do not wrap in ```json ... ```) matching the exact schema requested.
"""

def generate_advisory(station, forecast_horizon, aqi_category, dominant_source):
    """
    Generate multi-lingual citizen health advisories using an LLM.
    Falls back to a raw English dictionary if the LLM fails.
    """
    # 1. Fetch Ground Truth Guidance
    # Default to Moderate if somehow an unrecognized category appears
    base_guidance = CPCB_HEALTH_GUIDANCE.get(aqi_category, CPCB_HEALTH_GUIDANCE["Moderate"])
    
    # 2. Build Fallback JSON
    fallback_json = {
        "station": station,
        "forecast_horizon": forecast_horizon,
        "aqi_category": aqi_category,
        "dominant_source": dominant_source,
        "advisories": {
            "english": {
                "general_public": f"The air quality is {aqi_category}. Main pollution source is {dominant_source}. {base_guidance}",
                "sensitive_groups": f"Caution for sensitive groups: The air quality is {aqi_category} due to {dominant_source}. {base_guidance}"
            },
            "hindi": { "general_public": "Translation unavailable.", "sensitive_groups": "Translation unavailable." },
            "marathi": { "general_public": "Translation unavailable.", "sensitive_groups": "Translation unavailable." }
        },
        "guidance_source": "Based on CPCB National Air Quality Index standard health guidance categories"
    }

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found. Returning fallback advisory.")
        return fallback_json

    user_prompt = f"""
Given the following real-time air quality scenario, generate the advisory JSON.

Scenario:
- Station: {station}
- Forecast Horizon: {forecast_horizon}
- AQI Category: {aqi_category}
- Dominant Source: {dominant_source}
- Official CPCB Guidance Base: "{base_guidance}"

Construct a 2-3 sentence advisory incorporating the AQI severity, the main source ({dominant_source}), and the CPCB guidance.
Return a JSON object with this exact structure:
{{
  "station": "{station}",
  "forecast_horizon": "{forecast_horizon}",
  "aqi_category": "{aqi_category}",
  "dominant_source": "{dominant_source}",
  "advisories": {{
    "english": {{
      "general_public": "...",
      "sensitive_groups": "..."
    }},
    "hindi": {{
      "general_public": "...",
      "sensitive_groups": "..."
    }},
    "marathi": {{
      "general_public": "...",
      "sensitive_groups": "..."
    }}
  }},
  "guidance_source": "Based on CPCB National Air Quality Index standard health guidance categories"
}}
"""

    try:
        model = genai.GenerativeModel(
            model_name="gemini-3.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
        )
        
        response = model.generate_content(user_prompt)
        # Parse the JSON response
        result_json = json.loads(response.text.strip())
        return result_json
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        logger.warning("Falling back to standard English guidance.")
        return fallback_json

# ==========================================
# ISOLATED VALIDATION TEST
# ==========================================
if __name__ == "__main__":
    print("\n=======================================================")
    print("      CITIZEN ADVISORY AGENT - ISOLATED TEST           ")
    print("=======================================================\n")
    
    test_station = "Sion, Mumbai - MPCB"
    test_horizon = "24h"
    test_aqi = "Very Poor"
    test_source = "Traffic"
    
    logger.info(f"Running test case for Station: {test_station} | AQI: {test_aqi} | Source: {test_source}")
    
    result = generate_advisory(
        station=test_station,
        forecast_horizon=test_horizon,
        aqi_category=test_aqi,
        dominant_source=test_source
    )
    
    print("\n--- FINAL CITIZEN ADVISORY JSON ---\n")
    print(json.dumps(result, indent=2, ensure_ascii=True))
    
    with open("reports/citizen_advisory_test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("\n(Translations saved to reports/citizen_advisory_test.json with full Unicode)")
    print("\n=======================================================\n")
