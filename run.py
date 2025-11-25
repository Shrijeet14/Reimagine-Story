import subprocess
import sys
import os

def install_requirements():
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    print("Requirements installed successfully")

def create_directories():
    directories = [
        "outputs/chunks",
        "outputs/dna",
        "outputs/scenes",
        "outputs/final"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    try:
        install_requirements()
        create_directories()
        
        print("\nLaunching Story Reimagination System...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()