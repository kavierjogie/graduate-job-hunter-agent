import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file if it exists in the project root
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Extract and expose configuration variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def validate_config() -> None:
    """
    Validates that all required environment variables are present and valid.
    Raises a descriptive ValueError with actionable guidance if they are missing.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Check if missing, or if it is still the placeholder text from .env.example
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here", "your_key_here"):
        raise ValueError(
            "\n" + "=" * 80 + "\n"
            "CONFIGURATION ERROR: GEMINI_API_KEY environment variable is missing or invalid.\n\n"
            "To fix this issue, please follow these steps:\n"
            "  1. Create a file named '.env' in the project root directory:\n"
            f"     {PROJECT_ROOT}\\.env\n"
            "  2. Add your Gemini API key to that file:\n"
            "     GEMINI_API_KEY=your_actual_api_key_here\n"
            "  3. You can get a free API key from Google AI Studio at:\n"
            "     https://aistudio.google.com/\n"
            "  4. Ensure the key is NOT surrounded by quotes or brackets.\n"
            "  5. Save the file and restart the application.\n"
            "=" * 80
        )
