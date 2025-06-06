import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from scraper import scrape_website
from linkedin_finder import extract_linkedin_url, find_and_extract_linkedin_about
import linkedin_auth

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

@app.route('/batch', methods=['GET'])
def batch():
    """Render the batch processing page"""
    return render_template('batch.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle website scraping requests"""
    url = request.form.get('url')
    mode = request.form.get('mode', 'direct')  # Default to direct scraping
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    logger.debug(f"Scraping URL: {url} in mode: {mode}")
    
    try:
        # Direct scraping mode (LinkedIn or any website)
        if mode == 'direct':
            result = scrape_website(url)
            if result is None:
                flash('Failed to extract data from the website', 'danger')
                return redirect(url_for('index'))
            
            return render_template('results.html', data=result, url=url)
        
        # Find LinkedIn URL from company website and then scrape
        elif mode == 'find_linkedin':
            logger.info(f"Finding LinkedIn URL from website: {url}")
            linkedin_result = find_and_extract_linkedin_about(url)
            
            if not linkedin_result["success"]:
                flash(f'Failed to find LinkedIn profile: {linkedin_result["message"]}', 'danger')
                return redirect(url_for('index'))
            
            # We have LinkedIn data - prepare for display
            result = linkedin_result["company_data"]
            linkedin_url = linkedin_result["linkedin_url"]
            
            flash(f'Successfully found and extracted LinkedIn profile: {linkedin_url}', 'success')
            return render_template('results.html', 
                                  data=result, 
                                  url=url, 
                                  linkedin_url=linkedin_url,
                                  source_website=url)
        
        else:
            flash(f'Invalid scraping mode: {mode}', 'danger')
            return redirect(url_for('index'))
    
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
    mode = data.get('mode', 'direct')  # Default to direct scraping
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Direct scraping mode
        if mode == 'direct':
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
        
        # Find LinkedIn URL from website and then scrape it
        elif mode == 'find_linkedin':
            linkedin_result = find_and_extract_linkedin_about(url)
            
            if not linkedin_result["success"]:
                return jsonify({
                    'success': False,
                    'error': linkedin_result["message"],
                    'website_url': url,
                    'linkedin_url': linkedin_result.get('linkedin_url')
                }), 404
            
            return jsonify({
                'success': True,
                'website_url': url,
                'linkedin_url': linkedin_result["linkedin_url"],
                'data': linkedin_result["company_data"]
            })
            
        else:
            return jsonify({
                'success': False,
                'error': f'Invalid mode: {mode}. Use "direct" or "find_linkedin".'
            }), 400
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@app.route('/api/find_linkedin', methods=['POST'])
def api_find_linkedin():
    """API endpoint just for finding LinkedIn URLs without scraping them"""
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
        linkedin_url = extract_linkedin_url(url)
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': f'No LinkedIn URL found on website: {url}',
                'website_url': url
            }), 404
        
        return jsonify({
            'success': True,
            'website_url': url,
            'linkedin_url': linkedin_url
        })
    
    except Exception as e:
        logger.error(f"API find LinkedIn error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/linkedin-auth', methods=['GET', 'POST'])
def linkedin_auth_page():
    """Handle LinkedIn authentication for scraping"""
    # Check if we're already authenticated
    is_authenticated = linkedin_auth.is_authenticated()
    username = linkedin_auth.get_auth_username()
    auth_error = linkedin_auth.get_auth_error()
    
    # If this is a POST request (login attempt)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return render_template('linkedin_auth.html', 
                                  is_authenticated=is_authenticated,
                                  username=username,
                                  auth_error=auth_error)
        
        # Set credentials and try to authenticate
        linkedin_auth.set_credentials(username, password)
        auth_success = linkedin_auth.authenticate()
        
        if auth_success:
            flash('Successfully authenticated with LinkedIn!', 'success')
            return redirect(url_for('index'))
        else:
            # Authentication failed
            auth_error = linkedin_auth.get_auth_error()
            flash(f'Authentication failed: {auth_error}', 'danger')
            
            return render_template('linkedin_auth.html',
                                  is_authenticated=False,
                                  username=username,
                                  auth_error=auth_error)
    
    # GET request - show the login form
    return render_template('linkedin_auth.html',
                          is_authenticated=is_authenticated,
                          username=username,
                          auth_error=auth_error)

@app.route('/linkedin-logout', methods=['POST'])
def linkedin_logout():
    """Clear LinkedIn authentication"""
    linkedin_auth.clear_credentials()
    flash('LinkedIn credentials cleared', 'info')
    return redirect(url_for('index'))

@app.route('/api/linkedin-auth-status', methods=['GET'])
def api_linkedin_auth_status():
    """API endpoint for checking LinkedIn authentication status"""
    is_authenticated = linkedin_auth.is_authenticated()
    username = linkedin_auth.get_auth_username()
    auth_error = linkedin_auth.get_auth_error()
    
    return jsonify({
        'success': True,
        'is_authenticated': is_authenticated,
        'username': username,
        'auth_error': auth_error
    })

@app.route('/api/batch', methods=['POST'])
def api_batch_process():
    """API endpoint for batch processing multiple URLs"""
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'success': False,
            'error': 'URLs parameter is required as an array'
        }), 400
    
    urls = data['urls']
    mode = data.get('mode', 'find_linkedin')  # Default to find_linkedin mode
    
    if not isinstance(urls, list):
        return jsonify({
            'success': False,
            'error': 'URLs must be provided as an array'
        }), 400
    
    if len(urls) > 20:
        return jsonify({
            'success': False,
            'error': 'Maximum 20 URLs allowed in batch mode'
        }), 400
    
    results = []
    
    for url in urls:
        try:
            # Add http:// prefix if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Process based on mode
            if mode == 'find_linkedin':
                # Find LinkedIn URL and extract data
                result = find_and_extract_linkedin_about(url)
                
                if result["success"]:
                    results.append({
                        'success': True,
                        'website_url': url,
                        'linkedin_url': result["linkedin_url"],
                        'company_data': result["company_data"]
                    })
                else:
                    results.append({
                        'success': False,
                        'website_url': url,
                        'error': result["message"]
                    })
            
            elif mode == 'linkedin_only':
                # Just find LinkedIn URLs without extracting data
                linkedin_url = extract_linkedin_url(url)
                
                if linkedin_url:
                    results.append({
                        'success': True,
                        'website_url': url,
                        'linkedin_url': linkedin_url
                    })
                else:
                    results.append({
                        'success': False,
                        'website_url': url,
                        'error': 'No LinkedIn URL found'
                    })
            
            elif mode == 'direct':
                # Direct scraping of URLs (could be LinkedIn or any website)
                data = scrape_website(url)
                
                if data:
                    results.append({
                        'success': True,
                        'url': url,
                        'data': data
                    })
                else:
                    results.append({
                        'success': False,
                        'url': url,
                        'error': 'Failed to extract data'
                    })
            
            else:
                return jsonify({
                    'success': False,
                    'error': f'Invalid mode: {mode}. Use "find_linkedin", "linkedin_only", or "direct".'
                }), 400
                
        except Exception as e:
            logger.error(f"Batch processing error for URL {url}: {str(e)}")
            results.append({
                'success': False,
                'url': url,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'results': results,
        'total': len(urls),
        'successful': sum(1 for r in results if r.get('success', False)),
        'failed': sum(1 for r in results if not r.get('success', False))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
