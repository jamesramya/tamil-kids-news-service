from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sys
import json

template_dir = os.path.abspath('app/templates')
app = Flask(__name__, template_folder=template_dir)

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_json_file, save_json_file, ensure_dir_exists
from src.tts import generate_podcast_script, text_to_speech

app = Flask(__name__)

# Configuration
DATA_DIR = "data"
PROCESSED_NEWS_FILE = os.path.join(DATA_DIR, "processed_news.json")
APPROVED_NEWS_FILE = os.path.join(DATA_DIR, "approved_news.json")
PODCAST_SCRIPT_FILE = os.path.join(DATA_DIR, "podcast_script.txt")
PODCAST_AUDIO_FILE = os.path.join(DATA_DIR, "podcast.mp3")

# Ensure data directory exists
ensure_dir_exists(DATA_DIR)


@app.route('/')
def index():
    """Main page showing all articles for review"""
    articles = load_json_file(PROCESSED_NEWS_FILE, [])
    approved_count = sum(1 for article in articles
                         if article.get('approved', False))
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
        articles[article_id]['tamil_summary'] = request.form.get(
            'tamil_summary')
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
    approved_articles = [
        article for article in articles if article.get('approved', False)
    ]
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


@app.route('/generate-podcast', methods=['GET', 'POST'])
def generate_podcast():
    """Generate podcast from approved articles"""
    if request.method == 'POST':
        # Get all approved articles
        articles = load_json_file(PROCESSED_NEWS_FILE, [])
        approved_articles = [
            article for article in articles if article.get('approved', False)
        ]

        if not approved_articles:
            return jsonify({
                "status": "error",
                "message": "No approved articles found"
            })

        # Generate podcast script
        script = generate_podcast_script(approved_articles)

        # Save script to file
        with open(PODCAST_SCRIPT_FILE, 'w', encoding='utf-8') as f:
            f.write(script)

        # Attempt to generate audio (currently just a placeholder)
        audio_file = text_to_speech(script, PODCAST_AUDIO_FILE)

        result = {
            "status": "success",
            "script": script,
            "script_file": PODCAST_SCRIPT_FILE
        }

        if audio_file:
            result["audio_file"] = audio_file

        return jsonify(result)

    # GET request - show generation page
    return render_template('generate.html')


@app.route('/run-scraper', methods=['GET', 'POST'])
def run_scraper():
    """Run the news scraper"""
    if request.method == 'POST':
        try:
            # Import and run the main function from src.main
            from src.main import main
            main()
            return jsonify({
                "status": "success",
                "message": "Scraper ran successfully"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error running scraper: {str(e)}"
            })

    # GET request - show scraper page
    return render_template('scrapper.html')


if __name__ == '__main__':
    # Check if we're running on Replit
    if 'REPLIT_DB_URL' in os.environ:
        # Running on Replit - use 0.0.0.0 to make it accessible
        app.run(host='0.0.0.0', port=8080, debug=True)
    else:
        # Running locally
        app.run(debug=True)
