"""
LinkedIn Enhanced Scraper

This module extends the LinkedIn scraper functionality to extract:
1. Recent posts and their summaries
2. Job openings
3. Company people/employees
"""

import logging
import re
import urllib.request
from urllib.parse import urlparse, urljoin
import trafilatura
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_posts(linkedin_url):
    """
    Extract recent posts from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with posts information
    """
    logger.info(f"Extracting posts from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /posts to URL if not already present
    if not linkedin_url.endswith('/posts'):
        posts_url = linkedin_url.rstrip('/') + '/posts'
    else:
        posts_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(posts_url)
        if not downloaded:
            logger.error(f"Failed to download posts from: {posts_url}")
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Find post elements
        posts_data = {
            'count': 0,
            'posts': []
        }
        
        # Look for posts in different potential containers
        post_containers = []
        
        # Method 1: Look for post containers by class names commonly used by LinkedIn
        post_containers.extend(soup.find_all(['div', 'article'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['feed-shared-update', 'post-view', 'update-components', 'feed-item']
        )))
        
        # Method 2: Look for post containers with data attributes
        post_containers.extend(soup.find_all(['div', 'article'], attrs=lambda attrs: attrs and any(
            attr and 'post' in attr.lower() for attr in attrs
        )))
        
        # Check if any containers were found
        if not post_containers:
            logger.warning(f"No post containers found on: {posts_url}")
            
            # Attempt to get at least the count of posts
            count_element = soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*posts?', re.I))
            if count_element:
                count_match = re.search(r'(\d+)\s*posts?', count_element.text, re.I)
                if count_match:
                    posts_data['count'] = int(count_match.group(1))
                    logger.info(f"Found post count: {posts_data['count']}")
        
        # Process each post container
        unique_posts = set()  # To avoid duplicates
        
        for container in post_containers:
            # Extract post text
            post_text_element = container.find(['p', 'div', 'span'], class_=lambda c: c and any(
                term in str(c).lower() for term in ['feed-shared-text', 'update-text', 'post-text']
            ))
            
            if post_text_element and post_text_element.text.strip():
                post_text = post_text_element.text.strip()
                
                # Only add unique posts
                if post_text not in unique_posts:
                    unique_posts.add(post_text)
                    
                    # Create post object
                    post = {
                        'text': post_text[:250] + ('...' if len(post_text) > 250 else '')  # Limit to 250 chars
                    }
                    
                    # Try to find post date
                    date_element = container.find(['span', 'time'], string=re.compile(r'(ago|day|week|month|year|hour)', re.I))
                    if date_element:
                        post['date'] = date_element.text.strip()
                    
                    # Try to find engagement stats
                    reactions = container.find(['span', 'div'], string=re.compile(r'(\d+)\s*(reactions?|likes?)', re.I))
                    if reactions:
                        reaction_match = re.search(r'(\d+)\s*(reactions?|likes?)', reactions.text, re.I)
                        if reaction_match:
                            post['reactions'] = reaction_match.group(1)
                    
                    # Add to posts list
                    posts_data['posts'].append(post)
        
        # Update final count
        posts_data['count'] = len(posts_data['posts'])
        logger.info(f"Extracted {posts_data['count']} posts from {posts_url}")
        
        return posts_data
    
    except Exception as e:
        logger.error(f"Error extracting posts from {linkedin_url}: {str(e)}")
        return None

def extract_job_openings(linkedin_url):
    """
    Extract job openings from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with job openings information
    """
    logger.info(f"Extracting job openings from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /jobs to URL if not already present
    if not linkedin_url.endswith('/jobs'):
        jobs_url = linkedin_url.rstrip('/') + '/jobs'
    else:
        jobs_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(jobs_url)
        if not downloaded:
            logger.error(f"Failed to download jobs from: {jobs_url}")
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Initialize jobs data
        jobs_data = {
            'count': 0,
            'jobs': []
        }
        
        # Method 1: Look for job listings containers
        job_elements = []
        
        # Try to find job cards by common class names
        job_elements.extend(soup.find_all(['li', 'div'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['job-card', 'job-listing', 'job-result', 'jobs-search', 'job-item']
        )))
        
        # If no elements found using class-based approach, try other methods
        if not job_elements:
            # Try to find job title headers
            job_elements = soup.find_all(['h3', 'h4'], string=lambda s: s and len(s.strip()) > 0)
        
        # Extract total job count if available
        count_element = soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*jobs?', re.I))
        if count_element:
            count_match = re.search(r'(\d+)\s*jobs?', count_element.text, re.I)
            if count_match:
                jobs_data['count'] = int(count_match.group(1))
                logger.info(f"Found job count: {jobs_data['count']}")
        
        # Process job elements
        for element in job_elements:
            # For each job element, extract the title, location, and posting date if available
            
            # Extract job title
            job_title = element.get_text().strip()
            
            # Create basic job object
            job = {
                'title': job_title
            }
            
            # Try to find location
            location_element = element.find_next(['span', 'div'], string=re.compile(r'(remote|united states|usa|uk|canada|australia|india|germany|france)', re.I))
            if location_element:
                job['location'] = location_element.text.strip()
            
            # Try to find posting date
            date_element = element.find_next(['span', 'div'], string=re.compile(r'(posted|ago|day|week|month)', re.I))
            if date_element:
                job['date_posted'] = date_element.text.strip()
            
            # Add job to list if it has a title
            if job['title'] and len(job['title']) > 3:  # Minimum length to avoid noise
                jobs_data['jobs'].append(job)
        
        # If we didn't find a count earlier, use the length of discovered jobs
        if jobs_data['count'] == 0:
            jobs_data['count'] = len(jobs_data['jobs'])
        
        logger.info(f"Extracted {len(jobs_data['jobs'])} job openings from {jobs_url}")
        return jobs_data
    
    except Exception as e:
        logger.error(f"Error extracting job openings from {linkedin_url}: {str(e)}")
        return None

def extract_people(linkedin_url):
    """
    Extract people (employees, leadership) from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with people information
    """
    logger.info(f"Extracting people from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /people to URL if not already present
    if not linkedin_url.endswith('/people'):
        people_url = linkedin_url.rstrip('/') + '/people'
    else:
        people_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(people_url)
        if not downloaded:
            logger.error(f"Failed to download people from: {people_url}")
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Initialize people data
        people_data = {
            'employee_count': 0,
            'leaders': [],
            'locations': [],
            'departments': []
        }
        
        # Extract employee count (either from the people page or from previous data)
        count_element = soup.find(['span', 'div'], string=re.compile(r'(\d+[\,\d]*)\s*(employees?|people)', re.I))
        if count_element:
            count_match = re.search(r'(\d+[\,\d]*)\s*(employees?|people)', count_element.text, re.I)
            if count_match:
                # Remove commas and convert to int
                people_data['employee_count'] = int(count_match.group(1).replace(',', ''))
                logger.info(f"Found employee count: {people_data['employee_count']}")
        
        # Extract leadership/key people
        # Look for sections that might contain leadership titles
        leader_section = soup.find(['section', 'div'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['leadership', 'key-people', 'company-leaders', 'executives']
        ))
        
        leader_elements = []
        
        if leader_section:
            # Look for name elements within the leadership section
            leader_elements = leader_section.find_all(['h3', 'h4', 'a'], class_=lambda c: c and 'name' in str(c).lower())
        
        # If no specific leadership section found, look for job titles that suggest leadership
        if not leader_elements:
            # Look for job titles that indicate leadership positions
            leader_elements = soup.find_all(['div', 'span'], string=re.compile(r'(CEO|Chief|Director|VP|Head of|President|Founder)', re.I))
        
        # Process leadership elements
        for element in leader_elements:
            # For each leadership element, try to find the person's name and title
            
            name_element = element
            title_element = element.find_next(['div', 'span'], class_=lambda c: c and any(
                term in str(c).lower() for term in ['title', 'position', 'role']
            ))
            
            # If the element itself is the title, look for the name before it
            if re.search(r'(CEO|Chief|Director|VP|Head of|President|Founder)', element.text, re.I):
                title_element = element
                name_element = element.find_previous(['h3', 'h4', 'a', 'div', 'span'], class_=lambda c: c and 'name' in str(c).lower())
            
            # If we have a name element, extract the name and title
            if name_element:
                name = name_element.text.strip()
                title = title_element.text.strip() if title_element else ""
                
                # Add to leaders list if not already present
                if name and title:
                    leader = {
                        'name': name,
                        'title': title
                    }
                    
                    # Only add if not duplicate
                    if not any(l.get('name') == name for l in people_data['leaders']):
                        people_data['leaders'].append(leader)
        
        # Extract location information
        location_elements = soup.find_all(['div', 'span'], string=re.compile(r'(united states|usa|uk|canada|australia|india|germany|france)', re.I))
        
        for element in location_elements:
            location = element.text.strip()
            
            # Extract percentage if available
            next_element = element.find_next(['div', 'span'], string=re.compile(r'(\d+[\.\d]*\s*%)', re.I))
            percentage = next_element.text.strip() if next_element else ""
            
            # Add to locations if not already present
            location_item = {
                'location': location,
                'percentage': percentage
            }
            
            if not any(l.get('location') == location for l in people_data['locations']):
                people_data['locations'].append(location_item)
        
        # Extract department information
        department_elements = soup.find_all(['div', 'span'], string=re.compile(r'(engineering|sales|marketing|hr|finance|operations|product|design|research|development)', re.I))
        
        for element in department_elements:
            department = element.text.strip()
            
            # Extract percentage if available
            next_element = element.find_next(['div', 'span'], string=re.compile(r'(\d+[\.\d]*\s*%)', re.I))
            percentage = next_element.text.strip() if next_element else ""
            
            # Add to departments if not already present
            department_item = {
                'department': department,
                'percentage': percentage
            }
            
            if not any(d.get('department') == department for d in people_data['departments']):
                people_data['departments'].append(department_item)
        
        logger.info(f"Extracted people data: {len(people_data['leaders'])} leaders, {len(people_data['locations'])} locations, {len(people_data['departments'])} departments")
        return people_data
    
    except Exception as e:
        logger.error(f"Error extracting people from {linkedin_url}: {str(e)}")
        return None

def extract_all_enhanced_data(linkedin_url):
    """
    Extract all enhanced data: posts, jobs, and people
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with all enhanced data
    """
    enhanced_data = {}
    
    # Extract posts
    posts_data = extract_posts(linkedin_url)
    if posts_data:
        enhanced_data['posts'] = posts_data
    
    # Extract job openings
    jobs_data = extract_job_openings(linkedin_url)
    if jobs_data:
        enhanced_data['jobs'] = jobs_data
    
    # Extract people
    people_data = extract_people(linkedin_url)
    if people_data:
        enhanced_data['people'] = people_data
    
    return enhanced_data