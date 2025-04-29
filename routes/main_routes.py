"""
Main routes for LinkedIn Business Intelligence Extractor
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main landing page"""
    return render_template('index.html', redirect_url=request.args.get('redirect', '/'))

@main_bp.route('/extract')
def extract_data():
    """Render the LinkedIn extraction form page"""
    return render_template('linkedin_form.html')

@main_bp.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html')

@main_bp.route('/batch')
def batch():
    """Render the batch processing page"""
    return render_template('batch_form.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint for AWS Amplify"""
    return jsonify({
        'status': 'healthy',
        'service': 'LinkedIn Business Intelligence Extractor',
        'version': '1.0.0'
    })

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return redirect(url_for('static', filename=filename))