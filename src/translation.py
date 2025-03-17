import os
import re
from html import unescape
import time
import sys

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))  # Add parent directory to path

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect package not available. Will use basic language detection.")

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI package not available. Will use alternative translation methods.")

try:
    from google.cloud import translate_v2 as translate
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("Google Cloud Translation not available. Will use alternative translation methods.")

def clean_html(html_text):
    """Remove HTML tags and decode HTML entities"""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', html_text)
    # Decode HTML entities
    clean_text = unescape(clean_text)
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def basic_language_detection(text):
    """
    Very basic language detection for fallback when langdetect isn't available
    Only detects a few languages based on character sets
    """
    # Check for Tamil characters
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    if len(tamil_chars) > len(text) * 0.3:  # If >30% characters are Tamil
        return "ta"

    # Check for other Indian scripts (simplified)
    devanagari = re.findall(r'[\u0900-\u097F]', text)  # Hindi, Marathi, etc.
    if len(devanagari) > len(text) * 0.3:
        return "hi"  # Default to Hindi

    # Default to English for Latin script or unknown
    return "en"

def detect_language(text):
    """
    Detect the language of a text with retry

    Parameters:
    - text: The text to detect

    Returns:
    - Language code (e.g., 'en', 'ta')
    """
    if not text or len(text.strip()) < 10:
        return "unknown"

    # Clean text before detection
    text = clean_html(text)

    if not LANGDETECT_AVAILABLE:
        return basic_language_detection(text)

    # Try up to 3 times with langdetect
    for attempt in range(3):
        try:
            return detect(text)
        except Exception as e:
            print(f"Language detection error (attempt {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(1)  # Wait before retry

    # Fallback to basic detection if langdetect fails
    return basic_language_detection(text)

def translate_to_tamil_openai(text, api_key=None):
    """
    Translate text to conversational Tamil using OpenAI's models

    Parameters:
    - text: Text to translate
    - api_key: OpenAI API key (optional)

    Returns:
    - Translated text or None if translation failed
    """
    if not OPENAI_AVAILABLE:
        return None

    if api_key:
        client = OpenAI(api_key=api_key)
    elif 'OPENAI_API_KEY' in os.environ:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    else:
        print("OpenAI API key not found")
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly skilled translator. Translate the given text into conversational Tamil that would be easily understood by children. Keep the translation natural and appropriate for young audiences."},
                {"role": "user", "content": f"Translate this text to conversational Tamil suitable for children: \"{text}\""}
            ]
        )

        # Extract translated text from response
        translated_text = response.choices[0].message.content.strip()
        return translated_text

    except Exception as e:
        print(f"OpenAI translation error: {e}")
        return None

def translate_to_tamil_google(text):
    """
    Translate text to Tamil using Google Cloud Translation API

    Parameters:
    - text: Text to translate

    Returns:
    - Translated text or None if translation failed
    """
    if not GOOGLE_TRANSLATE_AVAILABLE:
        return None

    try:
        client = translate.Client()
        result = client.translate(text, target_language='ta')
        return result['translatedText']
    except Exception as e:
        print(f"Google translation error: {e}")
        return None

def translate_to_tamil_fallback(text):
    """
    Basic fallback translation method

    Parameters:
    - text: Text to translate

    Returns:
    - Simple translated text
    """
    # Clean the text first
    text = clean_html(text)

    print("Using basic fallback translation - output will be limited")
    # This is just a placeholder - in a real implementation you'd use a more robust fallback
    basic_translations = {
        "News": "செய்திகள்",
        "Today": "இன்று",
        "India": "இந்தியா",
        "World": "உலகம்",
        "Sports": "விளையாட்டு",
        "Health": "ஆரோக்கியம்",
        "Education": "கல்வி",
        "Weather": "வானிலை",
        "Politics": "அரசியல்",
        "Technology": "தொழில்நுட்பம்",
        "Science": "அறிவியல்",
        "Environment": "சுற்றுச்சூழல்",
        "Entertainment": "பொழுதுபோக்கு",
        "Business": "வணிகம்",
        "Economy": "பொருளாதாரம்",
        "Government": "அரசு"
    }

    # Very basic word replacement - this is NOT a proper translation
    result = text
    for eng, tam in basic_translations.items():
        result = result.replace(eng, tam)

    return f"[Need proper translation] {result}"

def translate_to_tamil(text):
    """
    Translate text to Tamil using preferred method with fallbacks

    Parameters:
    - text: Text to translate

    Returns:
    - Translated text
    """
    if not text:
        return ""

    # Clean the text first
    text = clean_html(text)

    if detect_language(text) == "ta":
        return text

    # Try OpenAI first if available
    translated = None
    if 'OPENAI_API_KEY' in os.environ:
        translated = translate_to_tamil_openai(text)
        if translated:
            return translated

    # Try Google Cloud Translation if available
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        translated = translate_to_tamil_google(text)
        if translated:
            return translated

    # Final fallback
    return translate_to_tamil_fallback(text)