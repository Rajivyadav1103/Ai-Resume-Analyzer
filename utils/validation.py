import os
import re
from pathlib import Path

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def ensure_directories(*paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_text(value):
    if value is None:
        return ""
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()
