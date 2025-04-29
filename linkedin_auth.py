"""
LinkedIn Authentication Module

This module handles authentication for LinkedIn to enable scraping with credentials.
It provides functions to:
1. Store LinkedIn credentials securely
2. Authenticate with LinkedIn
3. Fetch pages with authentication
"""

import os
import logging
import requests
import re
import urllib.request
from urllib.parse import urlparse
from http.cookiejar import CookieJar

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session to persist cookies
session = requests.Session()

# LinkedIn authentication state
auth_state = {
    'logged_in': False,
    'username': None,
    'error': None
}

def set_credentials(username, password):
    """
    Store LinkedIn credentials (without saving them to disk)
    
    Args:
        username: LinkedIn email/username
        password: LinkedIn password
        
    Returns:
        True if credentials were stored, False otherwise
    """
    if not username or not password:
        logger.warning("Empty LinkedIn credentials provided")
        auth_state['error'] = "Empty credentials provided"
        return False
    
    # Store credentials in memory
    auth_state['username'] = username
    # We store the password temporarily just for authentication
    auth_state['password'] = password
    auth_state['error'] = None
    
    logger.info(f"LinkedIn credentials set for user: {username}")
    return True

def clear_credentials():
    """Clear stored LinkedIn credentials"""
    auth_state['logged_in'] = False
    auth_state['username'] = None
    if 'password' in auth_state:
        del auth_state['password']  
    auth_state['error'] = None
    
    # Clear cookies
    session.cookies.clear()
    
    logger.info("LinkedIn credentials cleared")
    return True

def authenticate():
    """
    Authenticate with LinkedIn using stored credentials
    
    Returns:
        Authentication status (True=success, False=failure)
    """
    if 'username' not in auth_state or 'password' not in auth_state:
        logger.warning("No LinkedIn credentials found")
        auth_state['error'] = "No credentials provided"
        return False
    
    try:
        username = auth_state['username']
        password = auth_state['password']
        
        # Initial request to get CSRF token and cookies
        login_page = session.get('https://www.linkedin.com/login')
        
        # Extract CSRF token using regex
        csrf_token = None
        csrf_match = re.search(r'name="loginCsrfParam"\s+value="([^"]+)"', login_page.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
        
        if not csrf_token:
            logger.error("Could not extract CSRF token from LinkedIn login page")
            auth_state['error'] = "LinkedIn login form could not be processed"
            return False
        
        # Prepare login data
        login_data = {
            'session_key': username,
            'session_password': password,
            'loginCsrfParam': csrf_token
        }
        
        # Perform login
        login_response = session.post(
            'https://www.linkedin.com/checkpoint/lg/login-submit',
            data=login_data,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Referer': 'https://www.linkedin.com/login'
            }
        )
        
        # Check if login was successful
        if login_response.url.startswith('https://www.linkedin.com/feed/') or 'feed' in login_response.url:
            auth_state['logged_in'] = True
            logger.info(f"Successfully authenticated with LinkedIn as: {username}")
            
            # Clear password from memory after successful login
            del auth_state['password']
            
            return True
        else:
            # Check for various authentication issues
            if 'two-step-verification' in login_response.url:
                auth_state['error'] = "LinkedIn requires two-factor authentication - this is not currently supported"
                logger.warning("LinkedIn requires two-factor authentication")
            elif 'checkpoint' in login_response.url and 'challenge' in login_response.url:
                auth_state['error'] = "LinkedIn security checkpoint detected - please log in manually on LinkedIn.com first"
                logger.warning("LinkedIn security checkpoint detected")
            elif 'captcha' in login_response.url.lower() or 'captcha' in login_response.text.lower():
                auth_state['error'] = "LinkedIn is requiring CAPTCHA verification - please log in manually on LinkedIn.com first"
                logger.warning("LinkedIn CAPTCHA verification required")
            elif 'rate' in login_response.url.lower() or 'limit' in login_response.url.lower():
                auth_state['error'] = "LinkedIn rate limiting detected - please try again later"
                logger.warning("LinkedIn rate limiting detected")
            else:
                # Debug response for troubleshooting
                logger.warning(f"LinkedIn authentication failed - unexpected response URL: {login_response.url}")
                auth_state['error'] = "LinkedIn authentication failed - LinkedIn may be blocking automated logins for security"
            
            auth_state['logged_in'] = False
            # Clear password from memory after failed login
            del auth_state['password']
            
            return False
            
    except Exception as e:
        logger.error(f"Error during LinkedIn authentication: {str(e)}")
        auth_state['error'] = f"Authentication error: {str(e)}"
        auth_state['logged_in'] = False
        
        # Clear password from memory after exception
        if 'password' in auth_state:
            del auth_state['password']
            
        return False

def fetch_url_with_auth(url):
    """
    Fetch a LinkedIn URL with authentication
    
    Args:
        url: LinkedIn URL to fetch
        
    Returns:
        HTML content if successful, None otherwise
    """
    if not auth_state.get('logged_in', False):
        logger.warning("Cannot fetch URL with auth - not logged in")
        return None
    
    try:
        # Ensure we have the right URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        response = session.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Referer': 'https://www.linkedin.com/'
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched authenticated URL: {url}")
            return response.text
        else:
            logger.warning(f"Failed to fetch authenticated URL: {url} - Status: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching URL with auth: {str(e)}")
        return None

def is_authenticated():
    """
    Check if currently authenticated with LinkedIn
    
    Returns:
        Boolean indicating whether authenticated
    """
    return auth_state.get('logged_in', False)

def get_auth_username():
    """
    Get the current authenticated username
    
    Returns:
        Username if authenticated, None otherwise
    """
    return auth_state.get('username', None) if auth_state.get('logged_in', False) else None

def get_auth_error():
    """
    Get the current authentication error, if any
    
    Returns:
        Error message if authentication failed, None otherwise
    """
    return auth_state.get('error', None)