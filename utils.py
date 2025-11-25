import json
import re
import logging

logger = logging.getLogger(__name__)

def extract_json_from_response(response_text):
    logger.info("Extracting JSON from LLM response")
    
    text = response_text.strip()
    
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()
        logger.info("Stripped markdown code blocks from response")
    
    code_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_match:
        text = code_match.group(1).strip()
        logger.info("Stripped generic code blocks from response")
    
    try:
        parsed = json.loads(text)
        logger.info("Successfully parsed JSON response")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Attempted to parse: {text[:200]}...")
        return None

def validate_story_dna(dna):
    logger.info("Validating story DNA structure")
    
    if not dna:
        logger.error("DNA is None or empty")
        return False
    
    required_keys = ["characters", "events", "themes"]
    for key in required_keys:
        if key not in dna or not dna[key]:
            logger.error(f"DNA missing or empty key: {key}")
            return False
    
    if not isinstance(dna["characters"], list) or len(dna["characters"]) == 0:
        logger.error("DNA has no characters")
        return False
    
    if not isinstance(dna["events"], list) or len(dna["events"]) == 0:
        logger.error("DNA has no events")
        return False
    
    logger.info("DNA validation passed")
    return True

def validate_transformation_map(transform_map):
    logger.info("Validating transformation map")
    
    if not transform_map or "mappings" not in transform_map:
        logger.error("Transformation map is invalid or missing mappings")
        return False
    
    mappings = transform_map["mappings"]
    
    if not mappings.get("character_mappings"):
        logger.error("No character mappings found")
        return False
    
    if not mappings.get("conflict_mappings"):
        logger.error("No conflict mappings found")
        return False
    
    logger.info("Transformation map validation passed")
    return True

def validate_final_dna(dna):
    logger.info("Validating final story DNA")
    
    if not dna:
        logger.error("Final DNA is None or empty")
        return False
    
    required_keys = ["plot_arc", "characters", "themes", "critical_moments"]
    for key in required_keys:
        if key not in dna:
            logger.error(f"Final DNA missing key: {key}")
            return False
    
    if "plot_arc" in dna:
        arc_keys = ["setup", "conflict", "climax", "resolution"]
        for arc_key in arc_keys:
            if arc_key not in dna["plot_arc"]:
                logger.error(f"Plot arc missing: {arc_key}")
                return False
    
    if not dna.get("characters") or len(dna["characters"]) == 0:
        logger.error("Final DNA has no characters")
        return False
    
    if not dna.get("critical_moments") or len(dna["critical_moments"]) == 0:
        logger.error("Final DNA has no critical moments")
        return False
    
    logger.info("Final DNA validation passed")
    return True