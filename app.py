import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from scraper import scrape_website

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@app.route('/', methods=['GET'])
def index():
    """Render the main page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle website scraping requests"""
    url = request.form.get('url')
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    logger.debug(f"Scraping URL: {url}")
    
    try:
        result = scrape_website(url)
        if result is None:
            flash('Failed to extract data from the website', 'danger')
            return redirect(url_for('index'))
        
        return render_template('results.html', data=result, url=url)
    
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint for scraping websites"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL parameter is required'
        }), 400
    
    url = data['url']
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        result = scrape_website(url)
        if result is None:
            return jsonify({
                'success': False,
                'error': 'Failed to extract data from the website'
            }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
