import json
import logging
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import Config
from utils import extract_json_from_response, validate_story_dna, validate_final_dna

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StoryProcessor:
    def __init__(self, config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=1.0
        )
    
    def extract_text_from_pdf(self, pdf_path):
        logger.info(f"Extracting text from PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        logger.info(f"Extracted {len(text.split())} words from PDF")
        return text
    
    def chunk_text(self, text):
        logger.info("Chunking text into structured format")
        words = text.split()
        total_words = len(words)
        
        if total_words <= self.config.chunk_size:
            chunks = [[text]]
            self.config.save_output(chunks, "chunks.json", "chunks")
            logger.info(f"Created 1 chunk (short text)")
            return chunks
        
        paragraphs = text.split("\n\n")
        
        chunks = []
        current_page = []
        current_word_count = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_words = len(para.split())
            
            if current_word_count + para_words > self.config.chunk_size and current_page:
                chunks.append(current_page)
                current_page = []
                current_word_count = 0
            
            current_page.append(para)
            current_word_count += para_words
        
        if current_page:
            chunks.append(current_page)
        
        self.config.save_output(chunks, "chunks.json", "chunks")
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def generate_local_summary(self, chunk_paragraphs):
        chunk_text = "\n\n".join(chunk_paragraphs)
        
        prompt_config = self.config.get_prompt("local_summary")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_config["system"]),
            ("user", prompt_config["user"])
        ])
        
        chain = prompt | self.llm
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Generating local summary (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = chain.invoke({"chunk_text": chunk_text})
                parsed = extract_json_from_response(response.content)
                
                if parsed and validate_story_dna(parsed):
                    logger.info("Local summary generated successfully")
                    return parsed
                else:
                    logger.warning(f"Invalid DNA structure on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error generating local summary: {e}")
        
        logger.error("Failed to generate valid local summary after retries")
        return {
            "characters": [],
            "events": ["Failed to extract events"],
            "themes": []
        }
    
    def update_global_dna(self, current_dna, new_summary):
        prompt_config = self.config.get_prompt("rolling_dna_update")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_config["system"]),
            ("user", prompt_config["user"])
        ])
        
        chain = prompt | self.llm
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Updating global DNA (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = chain.invoke({
                    "current_dna": json.dumps(current_dna, indent=2),
                    "new_summary": json.dumps(new_summary, indent=2)
                })
                
                parsed = extract_json_from_response(response.content)
                
                if parsed and validate_story_dna(parsed):
                    logger.info("Global DNA updated successfully")
                    return parsed
                else:
                    logger.warning(f"Invalid DNA structure on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error updating global DNA: {e}")
        
        logger.error("Failed to update global DNA, returning current DNA")
        return current_dna
    
    def consolidate_final_dna(self, accumulated_dna):
        logger.info("Consolidating final story DNA")
        
        prompt_config = self.config.get_prompt("final_dna_consolidation")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_config["system"]),
            ("user", prompt_config["user"])
        ])
        
        chain = prompt | self.llm
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Consolidating final DNA (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = chain.invoke({
                    "accumulated_dna": json.dumps(accumulated_dna, indent=2)
                })
                
                parsed = extract_json_from_response(response.content)
                
                if parsed and validate_final_dna(parsed):
                    self.config.save_output(parsed, "final_dna.json", "dna")
                    logger.info("Final DNA consolidated and saved successfully")
                    return parsed
                else:
                    logger.warning(f"Invalid final DNA structure on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error consolidating final DNA: {e}")
        
        logger.error("Failed to consolidate final DNA after retries")
        return accumulated_dna
    
    def process_story(self, text_or_path):
        if text_or_path.endswith(".pdf"):
            text = self.extract_text_from_pdf(text_or_path)
        else:
            text = text_or_path
        
        chunks = self.chunk_text(text)
        
        logger.info("Generating local summaries")
        local_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            summary = self.generate_local_summary(chunk)
            local_summaries.append(summary)
        
        self.config.save_output(local_summaries, "local_summaries.json", "dna")
        
        logger.info("Building global DNA with rolling window")
        global_dna = {
            "characters": [],
            "events": [],
            "themes": []
        }
        
        for i, summary in enumerate(local_summaries):
            logger.info(f"Updating DNA with chunk {i+1}/{len(local_summaries)}")
            
            if i == 0:
                global_dna = summary
            else:
                global_dna = self.update_global_dna(global_dna, summary)
        
        final_dna = self.consolidate_final_dna(global_dna)
        return final_dna