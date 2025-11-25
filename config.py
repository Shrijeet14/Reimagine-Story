import json
import os
from dotenv import load_dotenv
from prompts import get_prompt

load_dotenv()

class Config:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = "gpt-4.1"
        self.chunk_size = 2000
        self.target_word_count = 1500
        self.scene_word_count = 400
        self.num_scenes = 4
        
        self.output_dirs = {
            "chunks": "outputs/chunks",
            "dna": "outputs/dna",
            "scenes": "outputs/scenes",
            "final": "outputs/final"
        }
    
    def get_prompt(self, prompt_name):
        return get_prompt(prompt_name)
    
    def save_output(self, content, filename, output_type):
        directory = self.output_dirs.get(output_type, "outputs")
        filepath = os.path.join(directory, filename)
        
        if isinstance(content, dict) or isinstance(content, list):
            with open(filepath, "w") as f:
                json.dump(content, f, indent=2)
        else:
            with open(filepath, "w") as f:
                f.write(content)
        
        return filepath
    
    def load_output(self, filename, output_type):
        directory = self.output_dirs.get(output_type, "outputs")
        filepath = os.path.join(directory, filename)
        
        if filepath.endswith(".json"):
            with open(filepath, "r") as f:
                return json.load(f)
        else:
            with open(filepath, "r") as f:
                return f.read()