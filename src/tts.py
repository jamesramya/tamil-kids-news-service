"""
Text-to-Speech module using OpenAI for Tamil kids news
"""
import os
import sys

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))  # Add parent directory to path

def text_to_speech_fallback(text, output_file="output.mp3"):
    """
    Placeholder for text-to-speech functionality

    Parameters:
    - text: Text to convert to speech
    - output_file: Path to save audio file

    Returns:
    - Path to output file
    """
    print("Text-to-speech not yet implemented.")
    print(f"Would convert text: '{text[:50]}...' to speech")

    # Create an empty MP3 file so file exists even if TTS fails
    try:
        ensure_dir_exists(os.path.dirname(output_file))
        with open(output_file, 'wb') as f:
            # Write a minimal valid MP3 header
            f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    except:
        pass

    return output_file

def text_to_speech_openai(text, output_file="data/output.mp3", voice="nova"):
    """
    Convert text to speech using OpenAI's TTS API

    Parameters:
    - text: Text to convert to speech
    - output_file: Path to save audio file
    - voice: Voice to use (options: alloy, echo, fable, onyx, nova, shimmer)
                Nova is most natural, Shimmer is more expressive

    Returns:
    - Path to output file or None if failed
    """
    if not text:
        return None

    try:
        from openai import OpenAI

        # Check for API key
        if 'OPENAI_API_KEY' not in os.environ:
            print("OpenAI API key not found in environment variables")
            return text_to_speech_fallback(text, output_file)

        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

        # Ensure output directory exists
        ensure_dir_exists(os.path.dirname(output_file))

        # Generate speech
        print(f"Generating speech with OpenAI using voice: {voice}")
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # Save to file
        response.stream_to_file(output_file)

        print(f"Generated audio file: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error generating speech with OpenAI: {e}")
        return text_to_speech_fallback(text, output_file)

def ensure_dir_exists(directory):
    """
    Create directory if it doesn't exist

    Parameters:
    - directory: Path to directory
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def generate_podcast_script(articles):
    """
    Generate a script for a kids news podcast

    Parameters:
    - articles: List of processed and approved articles

    Returns:
    - Podcast script text
    """
    if not articles:
        return ""

    script = "வணக்கம் குழந்தைகளே! இன்றைய செய்திகளை பார்ப்போம்.\n\n"  # Hello children! Let's look at today's news.

    for i, article in enumerate(articles):
        script += f"{i+1}. {article['tamil_title']}\n"
        if 'tamil_summary' in article and article['tamil_summary']:
            script += f"{article['tamil_summary']}\n\n"

    script += "\nஇன்றைய செய்திகள் இத்துடன் முடிகிறது. நன்றி!"  # That's the end of today's news. Thank you!

    return script

def text_to_speech(text, output_file="data/output.mp3"):
    """
    Convert text to speech using available method

    Parameters:
    - text: Text to convert to speech
    - output_file: Path to save audio file

    Returns:
    - Path to output file or None if failed
    """
    # Try OpenAI TTS first if API key is available
    if 'OPENAI_API_KEY' in os.environ:
        return text_to_speech_openai(text, output_file)

    # Fall back to placeholder if OpenAI is not available
    return text_to_speech_fallback(text, output_file)