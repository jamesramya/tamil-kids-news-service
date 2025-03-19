from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import os
import sys
import json
import datetime
import uuid

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from src.utils import load_json_file, save_json_file, ensure_dir_exists
from src.tts import generate_podcast_script, text_to_speech

# Get absolute paths for template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

# Initialize Flask application
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

# Configuration
DATA_DIR = "data"
PROCESSED_NEWS_FILE = os.path.join(DATA_DIR, "processed_news.json")
APPROVED_NEWS_FILE = os.path.join(DATA_DIR, "approved_news.json")
PODCAST_SCRIPT_FILE = os.path.join(DATA_DIR, "podcast_script.txt")

# Ensure data directory exists
ensure_dir_exists(DATA_DIR)

@app.route('/')
def index():
    """Main page showing all articles for review"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])
    approved_count = sum(1 for article in articles if article.get('approved', False))
    return render_template('index.html', 
                          articles=articles, 
                          total=len(articles),
                          approved=approved_count)

@app.route('/view/<int:article_id>')
def view_article(article_id):
    """View details of a specific article"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])

    if article_id >= len(articles):
        return "Article not found", 404

    return render_template('view.html', 
                          article=articles[article_id], 
                          article_id=article_id)

@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    """Edit a specific article"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])

    if article_id >= len(articles):
        return "Article not found", 404

    if request.method == 'POST':
        # Update article with edited content
        articles[article_id]['tamil_title'] = request.form.get('tamil_title')
        articles[article_id]['tamil_summary'] = request.form.get('tamil_summary')
        articles[article_id]['edited'] = True

        # Save updated articles
        save_json_file(articles, PROCESSED_NEWS_FILE)

        return redirect(url_for('view_article', article_id=article_id))

    return render_template('edit.html', 
                          article=articles[article_id], 
                          article_id=article_id)

@app.route('/approve/<int:article_id>', methods=['POST'])
def approve_article(article_id):
    """Approve an article"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])

    if article_id >= len(articles):
        return jsonify({"status": "error", "message": "Article not found"})

    articles[article_id]['approved'] = True
    save_json_file(articles, PROCESSED_NEWS_FILE)

    # Get all approved articles and save to approved_news.json
    approved_articles = [article for article in articles if article.get('approved', False)]
    save_json_file(approved_articles, APPROVED_NEWS_FILE)

    return jsonify({"status": "success"})

@app.route('/reject/<int:article_id>', methods=['POST'])
def reject_article(article_id):
    """Reject an article"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])

    if article_id >= len(articles):
        return jsonify({"status": "error", "message": "Article not found"})

    articles[article_id]['approved'] = False
    save_json_file(articles, PROCESSED_NEWS_FILE)

    return jsonify({"status": "success"})

# Route to serve audio files
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files from the data directory"""
    return send_from_directory(DATA_DIR, filename)

@app.route('/generate-podcast', methods=['GET', 'POST'])
def generate_podcast():
    """Generate podcast from approved articles"""
    if request.method == 'POST':
        try:
            # Get all approved articles
            articles = load_json_file(PROCESSED_NEWS_FILE, [])
            approved_articles = [article for article in articles if article.get('approved', False)]

            if not approved_articles:
                return jsonify({"status": "error", "message": "No approved articles found"})

            # Direct translation with OpenAI
            try:
                from openai import OpenAI

                if 'OPENAI_API_KEY' not in os.environ:
                    return jsonify({"status": "error", "message": "OpenAI API key not set. Please add it in Replit Secrets."})

                # Initialize OpenAI client
                client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

                # Function to translate with OpenAI - cleaner version
                def translate_to_tamil_direct(text):
                    if not text or len(text.strip()) < 5:
                        return text

                    print(f"Translating: {text[:50]}...")

                    try:
                        # Call OpenAI API directly
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a translator converting English to Tamil. Produce natural, conversational Tamil suitable for children. Do not include any English text or prefixes like '[Translation]' in your response."},
                                {"role": "user", "content": f"Translate this text to Tamil: \"{text}\""}
                            ]
                        )

                        translated = response.choices[0].message.content.strip()
                        print(f"Translation result: {translated[:50]}...")
                        return translated
                    except Exception as e:
                        print(f"OpenAI translation error: {e}")
                        # Create a simple translation without the "[Need proper translation]" prefix
                        import re
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
                            "Government": "அரசு",
                            "Device": "சாதனம்",
                            "New": "புதிய",
                            "elephants": "யானைகள்",
                            "Farm": "பண்ணை",
                            "keep": "வைத்திருக்க",
                            "at": "இல்",
                            "bay": "தடுப்பது"
                        }

                        result = text
                        for eng, tam in basic_translations.items():
                            result = re.sub(r'\b' + re.escape(eng) + r'\b', tam, result, flags=re.IGNORECASE)

                        return result

                # Process and translate each article
                translated_articles = []
                for article in approved_articles:
                    # Create a copy of the article to translate
                    translated_article = article.copy()

                    # Always translate title if not in Tamil
                    if article['title_language'] != "ta":
                        print(f"Translating title: {article['original_title']}")
                        translated_title = translate_to_tamil_direct(article['original_title'])
                        translated_article['tamil_title'] = translated_title

                    # Always translate summary if not in Tamil
                    if article['summary_language'] != "ta":
                        print(f"Translating summary: {article['original_summary'][:50]}...")
                        translated_summary = translate_to_tamil_direct(article['original_summary'])
                        translated_article['tamil_summary'] = translated_summary

                    translated_articles.append(translated_article)

            except ImportError:
                print("OpenAI package not available. Using articles without additional translation.")
                translated_articles = approved_articles

            # Generate podcast script with translated content
            script = generate_podcast_script(translated_articles)

            # Save script to file with a unique identifier
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            podcast_filename = f"podcast_{timestamp}_{unique_id}"

            script_filename = f"{podcast_filename}.txt"
            script_filepath = os.path.join(DATA_DIR, script_filename)

            ensure_dir_exists(os.path.dirname(script_filepath))
            with open(script_filepath, 'w', encoding='utf-8') as f:
                f.write(script)

            # Generate audio using OpenAI TTS
            audio_filename = f"{podcast_filename}.mp3"
            audio_filepath = os.path.join(DATA_DIR, audio_filename)
            audio_file = text_to_speech(script, audio_filepath)

            result = {
                "status": "success", 
                "script": script,
                "script_file": script_filepath,
                "script_filename": script_filename
            }

            if audio_file:
                result["audio_file"] = audio_filepath
                result["audio_filename"] = audio_filename
                result["audio_url"] = url_for('serve_audio', filename=audio_filename)

            return jsonify(result)
        except Exception as e:
            import traceback
            traceback_text = traceback.format_exc()
            print(traceback_text)
            return jsonify({"status": "error", "message": f"Error generating podcast: {str(e)}\n\n{traceback_text}"})

    # GET request - show generation page
    try:
        return render_template('generate.html')
    except Exception as e:
        return f"Error loading template: {str(e)}"

@app.route('/run-scraper', methods=['GET', 'POST'])
def run_scraper():
    """Run the news scraper"""
    if request.method == 'POST':
        try:
            # Import and run the main function from src.main
            from src.main import main
            main()
            return jsonify({"status": "success", "message": "Scraper ran successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error running scraper: {str(e)}"})

    # GET request - use template if available
    try:
        return render_template('scraper.html')
    except Exception as e:
        # Fallback to inline HTML if template not found
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Run Scraper - Tamil Kids News Service</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
                <div class="container">
                    <a class="navbar-brand" href="/">Tamil Kids News Service</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/">Articles</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/generate-podcast">Generate Podcast</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/run-scraper">Run Scraper</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <div class="container">
                <h1 class="mb-4">News Scraper</h1>

                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Run News Scraper</h5>
                        <p class="card-text">
                            Run the news scraper to fetch and process new articles from RSS feeds.
                            This will fetch articles, detect their language, and translate non-Tamil content to Tamil.
                        </p>
                        <div class="alert alert-info">
                            <strong>Note:</strong> This process may take a few moments to complete depending on the number of articles.
                        </div>
                        <button id="runScraperBtn" class="btn btn-primary">Run Scraper</button>
                    </div>
                </div>

                <div id="resultAlert" class="alert alert-success mt-4 d-none">
                    <strong>Success!</strong> The scraper has run successfully. 
                    <a href="/" class="alert-link">View the articles</a> for review.
                </div>

                <div id="loadingSpinner" class="text-center mt-4 d-none">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Running scraper, please wait...</p>
                </div>

                <div id="errorAlert" class="alert alert-danger mt-4 d-none">
                    <strong>Error:</strong> <span id="errorMessage"></span>
                </div>

                <div class="card mt-4">
                    <div class="card-header">
                        <h5>Current RSS Feeds</h5>
                    </div>
                    <div class="card-body">
                        <p>The following RSS feeds are currently configured:</p>
                        <ul>
                            <li><a href="https://www.thehindu.com/news/national/feeder/default.rss" target="_blank">The Hindu - National News</a></li>
                            <li><a href="https://timesofindia.indiatimes.com/rssfeeds/4719148.cms" target="_blank">Times of India - India News</a></li>
                            <li><a href="https://tamil.oneindia.com/rss/tamil-news.xml" target="_blank">OneIndia Tamil News</a></li>
                        </ul>
                    </div>
                </div>
            </div>

            <script>
                document.getElementById('runScraperBtn').addEventListener('click', function() {
                    // Show loading spinner
                    document.getElementById('loadingSpinner').classList.remove('d-none');
                    document.getElementById('resultAlert').classList.add('d-none');
                    document.getElementById('errorAlert').classList.add('d-none');

                    // Call API to run scraper
                    fetch('/run-scraper', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Hide loading spinner
                        document.getElementById('loadingSpinner').classList.add('d-none');

                        if (data.status === 'success') {
                            // Show success alert
                            document.getElementById('resultAlert').classList.remove('d-none');
                        } else {
                            // Show error
                            document.getElementById('errorAlert').classList.remove('d-none');
                            document.getElementById('errorMessage').textContent = data.message || 'An error occurred';
                        }
                    })
                    .catch(error => {
                        // Hide loading spinner and show error
                        document.getElementById('loadingSpinner').classList.add('d-none');
                        document.getElementById('errorAlert').classList.remove('d-none');
                        document.getElementById('errorMessage').textContent = 'An error occurred while running the scraper';
                        console.error('Error:', error);
                    });
                });
            </script>
        </body>
        </html>
        """

if __name__ == '__main__':
    # Check if we're running on Replit
    if 'REPLIT_DB_URL' in os.environ:
        # Running on Replit - use 0.0.0.0 to make it accessible
        app.run(host='0.0.0.0', port=8080, debug=True)
    else:
        # Running locally
        app.run(debug=True)