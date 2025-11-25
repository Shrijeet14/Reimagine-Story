import json
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import Config
from utils import extract_json_from_response, validate_transformation_map

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorldBuilder:
    def __init__(self, config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=1.0
        )
    
    def define_new_world(self, story_dna, user_world_choice):
        logger.info(f"Defining new world: {user_world_choice}")
        
        prompt_config = self.config.get_prompt("world_definition")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_config["system"]),
            ("user", prompt_config["user"])
        ])
        
        chain = prompt | self.llm
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Defining world (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = chain.invoke({
                    "themes": json.dumps(story_dna.get("themes", [])),
                    "user_world_choice": user_world_choice
                })
                
                parsed = extract_json_from_response(response.content)
                
                if parsed:
                    logger.info("New world defined successfully")
                    return parsed
                else:
                    logger.warning(f"Failed to parse world definition on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error defining new world: {e}")
        
        logger.error("Failed to define new world, using fallback")
        return {
            "setting": user_world_choice,
            "era": "contemporary",
            "technology_or_magic": [],
            "culture": "diverse",
            "tone": "balanced",
            "world_rules": []
        }
    
    def create_transformation_map(self, story_dna, new_world):
        logger.info("Creating transformation mappings")
        
        prompt_config = self.config.get_prompt("transformation_mapping")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_config["system"]),
            ("user", prompt_config["user"])
        ])
        
        chain = prompt | self.llm
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Creating transformation map (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = chain.invoke({
                    "story_dna": json.dumps(story_dna, indent=2),
                    "new_world": json.dumps(new_world, indent=2)
                })
                
                parsed = extract_json_from_response(response.content)
                
                if parsed:
                    full_map = {
                        "new_world": new_world,
                        "mappings": parsed
                    }
                    
                    if validate_transformation_map(full_map):
                        self.config.save_output(full_map, "transformation_map.json", "dna")
                        logger.info("Transformation map created and saved successfully")
                        return full_map
                    else:
                        logger.warning(f"Invalid transformation map on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error creating transformation map: {e}")
        
        logger.error("Failed to create transformation map, using empty mappings")
        return {
            "new_world": new_world,
            "mappings": {
                "character_mappings": {},
                "conflict_mappings": {},
                "preserved_dynamics": []
            }
        }
    
    def build_new_world(self, story_dna, user_world_choice):
        new_world = self.define_new_world(story_dna, user_world_choice)
        transformation_map = self.create_transformation_map(story_dna, new_world)
        return transformation_map