# import os
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent


# class Config:
#     SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
#     SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'resume_analyzer.db'}")
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
#     REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", str(BASE_DIR / "reports"))
#     MAX_CONTENT_LENGTH = 5 * 1024 * 1024
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")




import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'resume_analyzer.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "uploads")
    )

    REPORTS_FOLDER = os.getenv(
        "REPORTS_FOLDER",
        str(BASE_DIR / "reports")
    )

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    