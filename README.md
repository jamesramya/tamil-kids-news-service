# Tamil Kids News Service

A service that scrapes latest headlines, translates them to Tamil, and converts them to spoken audio for children.

## Project Overview

This project aims to create age-appropriate news content for Tamil-speaking children. It follows these steps:

1. Scrapes news from various RSS feeds
2. Detects the language of each article
3. Translates non-Tamil content to conversational Tamil
4. Provides a review interface for quality control
5. Converts approved content to speech
6. Packages everything as a podcast

## Setup on Replit

The easiest way to run this project is on Replit:

1. Create a Replit account if you don't have one
2. Click "Create Repl" → Choose "Import from GitHub"
3. Enter your repository URL
4. Replit will automatically set up the environment
5. Click "Run" to start the application

### Setting Up Translation APIs (Optional)

For better translation quality:

1. Create an OpenAI API key at https://platform.openai.com/account/api-keys
2. Add it to Replit Secrets (Tools → Secrets) with the name `OPENAI_API_KEY`

## Project Structure

- `src/` - Core processing scripts
  - `main.py` - Main script for news fetching
  - `translation.py` - Language detection and translation
  - `utils.py` - Utility functions
  - `tts.py` - Text-to-speech conversion (placeholder)

- `app/` - Flask web application
  - `app.py` - Main Flask application
  - `templates/` - HTML templates

- `data/` - Stores processed news and generated audio (not committed to Git)

## Using the Application

1. **Run the Scraper**: Use the "Run Scraper" page to fetch latest news
2. **Review Articles**: On the main page, review and edit the translated content
3. **Generate Podcast**: Once articles are approved, generate the podcast script

## Current Limitations

- Basic translation without API keys
- Text-to-speech not fully implemented yet
- Limited error handling

## Future Plans

- Automated daily scraping
- Podcast feed generation
- Mobile app for easy listening
- Personalized content based on age and interests
