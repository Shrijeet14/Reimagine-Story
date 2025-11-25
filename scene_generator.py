import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import Config
from utils import extract_json_from_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SceneGenerator:
    def __init__(self, config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=1.0
        )
    
    def select_key_moments(self, story_dna):
        critical_moments = story_dna.get("critical_moments", [])
        
        if len(critical_moments) <= self.config.num_scenes:
            return critical_moments
        
        total = len(critical_moments)
        selected_indices = [0, total - 1]
        
        remaining = self.config.num_scenes - 2
        if remaining > 0:
            step = (total - 2) / (remaining + 1)
            for i in range(1, remaining + 1):
                idx = int(i * step)
                selected_indices.insert(i, idx)
        
        selected_moments = [critical_moments[i] for i in sorted(selected_indices)]
        return selected_moments
    
    def create_scene_plan(self, story_dna):
        logger.info("Creating scene plan")
        
        moments = self.select_key_moments(story_dna)
        positions = ["opening", "rising", "climax", "resolution"]
        
        scene_plan = []
        for i, moment in enumerate(moments):
            position = positions[i] if i < len(positions) else "middle"
            scene_plan.append({
                "position": position,
                "source_moment": moment,
                "index": i
            })
        
        logger.info(f"Scene plan created with {len(scene_plan)} scenes")
        return scene_plan
    
    def generate_scene(self, story_dna, transformation_map, scene_info, previous_summary=None):
        position = scene_info["position"]
        logger.info(f"Generating scene: {position}")
        
        requirements_map = {
            "opening": ["establish world", "introduce protagonist", "show initial situation"],
            "rising": ["escalate conflict", "develop tension", "advance plot"],
            "climax": ["reach peak tension", "critical decision point", "turning point"],
            "resolution": ["resolve main conflict", "show transformation", "conclude arc"]
        }
        
        requirements = requirements_map.get(position, ["advance story"])
        requirements_str = ", ".join(requirements)
        
        previous_context = ""
        if previous_summary:
            previous_context = f"Previous scene summary: {previous_summary}\nEnsure continuity with this."
        else:
            previous_context = "This is the opening scene."
        
        # Get the base prompts
        prompt_config = self.config.get_prompt("scene_generation")
        
        # Build messages directly using f-strings - NO TEMPLATES
        system_prompt = prompt_config["system"]
        
        story_dna_str = json.dumps(story_dna, indent=2)
        transformation_map_str = json.dumps(transformation_map, indent=2)
        
        user_prompt = f"""Story DNA:
{story_dna_str}

New World & Characters:
{transformation_map_str}

Scene Position: {position}
Target word count: {self.config.scene_word_count}
Must accomplish: {requirements_str}

{previous_context}

Write the scene using the transformed characters and new world setting.
Then provide a 2-3 sentence summary.

Output ONLY valid JSON with two keys: scene_text and scene_summary"""
        
        # Call LLM directly with messages - NO TEMPLATE
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Generating scene (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = self.llm.invoke(messages)
                
                parsed = extract_json_from_response(response.content)
                
                if parsed and "scene_text" in parsed:
                    scene_text = parsed.get("scene_text", response.content)
                    scene_summary = parsed.get("scene_summary", f"Scene {position} completed")
                    logger.info(f"Scene {position} generated successfully")
                    return {
                        "text": scene_text,
                        "summary": scene_summary,
                        "position": position
                    }
                else:
                    logger.warning(f"Failed to parse scene on attempt {attempt + 1}, using raw text")
                    return {
                        "text": response.content,
                        "summary": f"Scene {position} completed",
                        "position": position
                    }
            except Exception as e:
                logger.error(f"Error generating scene: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.error(f"Failed to generate scene {position} after retries")
        return {
            "text": f"Scene {position} could not be generated.",
            "summary": f"Scene {position} failed",
            "position": position
        }
    
    def polish_story(self, scenes, story_dna):
        logger.info("Polishing final story")
        
        all_scenes_text = "\n\n---SCENE BREAK---\n\n".join([s["text"] for s in scenes])
        
        prompt_config = self.config.get_prompt("final_polish")
        
        # Build messages directly - NO TEMPLATE
        system_prompt = prompt_config["system"]
        user_prompt = f"""Scenes to combine:

{all_scenes_text}

Story DNA for reference:
{json.dumps(story_dna, indent=2)}

Combine these scenes with smooth transitions into a complete, polished story. Output the final story text only (no JSON)."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        final_story = response.content
        
        self.config.save_output(final_story, "final_story.txt", "final")
        logger.info("Final story saved")
        return final_story
    
    def generate_full_story(self, story_dna, transformation_map):
        scene_plan = self.create_scene_plan(story_dna)
        
        scenes = []
        previous_summary = None
        
        for scene_info in scene_plan:
            scene = self.generate_scene(
                story_dna,
                transformation_map,
                scene_info,
                previous_summary
            )
            scenes.append(scene)
            previous_summary = scene["summary"]
            
            self.config.save_output(
                scene,
                f"scene_{scene_info['index']}_{scene_info['position']}.json",
                "scenes"
            )
        
        final_story = self.polish_story(scenes, story_dna)
        return final_story