import streamlit as st
import os
from config import Config
from story_processor import StoryProcessor
from world_builder import WorldBuilder
from scene_generator import SceneGenerator

st.set_page_config(page_title="Story Reimagination System", layout="wide")

st.title("Story Reimagination System")
st.markdown("Transform classic stories into new worlds using AI")

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input(
    "Enter OpenAI API Key (optional if set in .env):",
    type="password",
    value=st.session_state.api_key
)

if api_key:
    st.session_state.api_key = api_key
    os.environ["OPENAI_API_KEY"] = api_key

col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Source Story")
    
    input_method = st.radio(
        "Choose input method:",
        ["Paste Text", "Upload PDF"]
    )
    
    source_text = None
    
    if input_method == "Paste Text":
        source_text = st.text_area(
            "Paste your story here:",
            height=300,
            placeholder="Enter the complete text of your source story..."
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload PDF file:",
            type=["pdf"]
        )
        if uploaded_file:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            source_text = temp_path

with col2:
    st.subheader("Define New World")
    
    setting_type = st.selectbox(
        "1. Setting Type:",
        [
            "Sci-fi",
            "Fantasy",
            "Historical",
            "Modern",
            "Post-apocalyptic",
            "Cyberpunk",
            "Steampunk",
            "Space Opera",
            "Dystopian",
            "Other"
        ]
    )
    
    specific_setting = st.text_input(
        "2. Specific Setting:",
        placeholder="e.g., Mars colony, Medieval castle, 1920s New York, Underground bunker..."
    )
    
    time_period = st.text_input(
        "3. Time Period:",
        placeholder="e.g., 2147, 1920s, Medieval era, Year 3000, Present day..."
    )
    
    tone = st.selectbox(
        "4. Tone:",
        [
            "Dark/Gritty",
            "Hopeful",
            "Satirical",
            "Serious",
            "Comedic",
            "Mysterious",
            "Romantic",
            "Epic"
        ]
    )
    
    key_feature = st.text_input(
        "5. Key Feature (optional):",
        placeholder="e.g., Corporate dystopia, Magic system, Prohibition era, AI uprising..."
    )
    
    new_world_description = st.text_area(
        "6. Additional Description (optional):",
        placeholder="Add any other details about your reimagined world...",
        height=100
    )
    
    st.markdown("---")
    st.caption("All inputs will be combined to create your new world")

st.markdown("---")

if st.button("Reimagine Story", type="primary", disabled=not (source_text and specific_setting and time_period)):
    
    if not source_text:
        st.error("Please provide source story")
    elif not specific_setting:
        st.error("Please specify the setting")
    elif not time_period:
        st.error("Please specify the time period")
    else:
        new_world_parts = [
            f"Setting Type: {setting_type}",
            f"Specific Setting: {specific_setting}",
            f"Time Period: {time_period}",
            f"Tone: {tone}"
        ]
        
        if key_feature:
            new_world_parts.append(f"Key Feature: {key_feature}")
        
        if new_world_description:
            new_world_parts.append(f"Additional Details: {new_world_description}")
        
        new_world = " | ".join(new_world_parts)
        try:
            config = Config()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Step 1/5: Extracting and chunking story...")
            progress_bar.progress(10)
            processor = StoryProcessor(config)
            story_dna = processor.process_story(source_text)
            
            status_text.text("Step 2/5: Analyzing story DNA...")
            progress_bar.progress(30)
            
            st.success("Story DNA extracted successfully")
            with st.expander("View Story DNA"):
                st.json(story_dna)
            
            status_text.text("Step 3/5: Building new world...")
            progress_bar.progress(50)
            builder = WorldBuilder(config)
            transformation_map = builder.build_new_world(story_dna, new_world)
            
            st.success("World transformation map created")
            with st.expander("View Transformation Map"):
                st.json(transformation_map)
            
            status_text.text("Step 4/5: Generating scenes...")
            progress_bar.progress(70)
            generator = SceneGenerator(config)
            final_story = generator.generate_full_story(story_dna, transformation_map)
            
            status_text.text("Step 5/5: Polishing final story...")
            progress_bar.progress(90)
            
            progress_bar.progress(100)
            status_text.text("Complete!")
            
            st.markdown("---")
            st.subheader("Reimagined Story")
            
            st.markdown(final_story)
            
            st.download_button(
                label="Download Story",
                data=final_story,
                file_name="reimagined_story.txt",
                mime="text/plain"
            )
            
            if input_method == "Upload PDF" and os.path.exists(source_text):
                os.remove(source_text)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if input_method == "Upload PDF" and os.path.exists(source_text):
                os.remove(source_text)

st.markdown("---")