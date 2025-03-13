import os
import re
from html import unescape

def ensure_dir_exists(directory):
    """
    Create directory if it doesn't exist

    Parameters:
    - directory: Path to directory
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def clean_html(html_text):
    """
    Remove HTML tags and decode HTML entities

    Parameters:
    - html_text: HTML text to clean

    Returns:
    - Cleaned text
    """
    if not html_text:
        return ""

    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', html_text)
    # Decode HTML entities
    clean_text = unescape(clean_text)
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def truncate_text(text, max_length=100, add_ellipsis=True):
    """
    Truncate text to a maximum length

    Parameters:
    - text: Text to truncate
    - max_length: Maximum length in characters
    - add_ellipsis: Whether to add ellipsis at the end

    Returns:
    - Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    truncated = text[:max_length].strip()
    if add_ellipsis:
        truncated += "..."

    return truncated

def load_json_file(filepath, default=None):
    """
    Load JSON file with error handling

    Parameters:
    - filepath: Path to JSON file
    - default: Default value to return if file doesn't exist or is invalid

    Returns:
    - Parsed JSON data or default value
    """
    import json

    if not default:
        default = []

    if not os.path.exists(filepath):
        return default

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return default

def save_json_file(data, filepath):
    """
    Save data to JSON file with error handling

    Parameters:
    - data: Data to save
    - filepath: Path to JSON file

    Returns:
    - True if successful, False otherwise
    """
    import json

    ensure_dir_exists(os.path.dirname(filepath))

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file {filepath}: {e}")
        return False