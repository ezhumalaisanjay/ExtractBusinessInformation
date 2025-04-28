import re
import urllib.request
import logging
import trafilatura
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
from html.parser import HTMLParser

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom HTML Parser class based on the uploaded file
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.contact_info = []
        self.services = []
        self.products = []
        self.company_name = None
        self.capture = False
        self.headings = []  # Store heading data to analyze better
        self.current_tag = None  # Track the current tag being processed

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag  # Track the current tag
        if tag == 'p' or tag == 'a':
            self.capture = True
        elif tag == 'h1' or tag == 'h2' or tag == 'h3':
            self.capture = True  # Capture text in headers (for potential company name)

    def handle_endtag(self, tag):
        if tag == 'p' or tag == 'a' or tag == 'h1' or tag == 'h2' or tag == 'h3':
            self.capture = False
        self.current_tag = None  # Reset current tag when ending a tag

    def handle_data(self, data):
        if self.capture:
            text = data.strip()
            if self.current_tag in ['h1', 'h2', 'h3']:
                self.headings.append(text)
            # Check for company name: First heading tag or the title of the page
            if not self.company_name and self.headings:
                self.company_name = self.headings[0]  # Select the first heading as the company name
            # Check for contact info (email, phone, address)
            elif re.search(r'[\w\.-]+@[\w\.-]+', text):
                self.contact_info.append(text)
            elif re.search(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}', text):
                self.contact_info.append(text)
            elif re.search(r'\d{1,4}[\w\s]+[,\-.\d]*\s*(Street|Ave|Road|Boulevard|Lane)', text):
                self.contact_info.append(text)
            elif 'service' in text.lower():
                self.services.append(text)
            elif 'product' in text.lower() or 'offer' in text.lower():
                self.products.append(text)
            else:
                self.paragraphs.append(text)

# Regular expressions for data extraction
EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
PHONE_PATTERN = r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
ADDRESS_PATTERN = r'\d+\s+(?:[A-Za-z0-9.-]+\s+){1,5}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq)'
SOCIAL_MEDIA_PATTERNS = {
    'facebook': r'facebook\.com/[\w.-]+',
    'twitter': r'twitter\.com/[\w.-]+',
    'linkedin': r'linkedin\.com/(?:company|in)/[\w.-]+',
    'instagram': r'instagram\.com/[\w.-]+',
}

def extract_emails(text):
    """Extract email addresses from text"""
    emails = re.findall(EMAIL_PATTERN, text)
    return list(set(emails))  # Remove duplicates

def extract_phones(text):
    """Extract phone numbers from text"""
    phones = re.findall(PHONE_PATTERN, text)
    return list(set(phones))  # Remove duplicates

def extract_addresses(text):
    """Extract physical addresses from text"""
    addresses = re.findall(ADDRESS_PATTERN, text, re.IGNORECASE)
    return list(set(addresses))  # Remove duplicates

def extract_social_media(text):
    """Extract social media links from text"""
    social_media = {}
    for platform, pattern in SOCIAL_MEDIA_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            social_media[platform] = list(set(matches))
    return social_media

def clean_text(text):
    """Clean text by removing extra whitespace and normalizing newlines"""
    if not text:
        return ""
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_company_name(soup, domain_name):
    """Extract company name using multiple methods"""
    # Method 1: Look for title tag
    title = soup.title.string if soup.title else None
    
    # Method 2: Look for logo alt text
    logo = soup.find('img', alt=re.compile(r'logo', re.I))
    logo_alt = logo.get('alt') if logo else None
    
    # Method 3: Look for heading in header
    header = soup.find('header')
    header_heading = None
    if header:
        heading = header.find(['h1', 'h2'])
        header_heading = heading.text.strip() if heading else None
    
    # Method 4: First h1 on the page
    first_h1 = soup.find('h1')
    first_h1_text = first_h1.text.strip() if first_h1 else None
    
    # Method 5: Use the domain name
    domain_parts = domain_name.split('.')
    domain_company = domain_parts[0].title() if domain_parts else None
    
    # Select the best company name
    candidates = [
        name for name in [header_heading, first_h1_text, logo_alt, title, domain_company]
        if name and len(name) < 100
    ]
    
    if candidates:
        # Choose the shortest name as it's likely most accurate
        return min(candidates, key=len)
    return domain_company or "Unknown Company"

def extract_services_products(text, company_name):
    """Extract services and products from text"""
    # Look for sections about services or products
    services = []
    products = []
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n+', text)
    
    for para in paragraphs:
        para = clean_text(para)
        
        # Services often contain these keywords
        if re.search(r'\b(service|solution|offering|expertise|consulting|support)\b', para, re.I):
            if len(para) > 20 and len(para) < 500:  # Avoid too short or too long paragraphs
                services.append(para)
        
        # Products often contain these keywords
        if re.search(r'\b(product|tool|software|platform|app|application)\b', para, re.I):
            if len(para) > 20 and len(para) < 500:  # Avoid too short or too long paragraphs
                products.append(para)
    
    # Limit to top 5 most relevant services and products
    services = services[:5]
    products = products[:5]
    
    return services, products

def extract_company_history(text, company_name):
    """Extract company history, founding date, and other significant information"""
    history_info = {}
    
    # Split text into paragraphs for analysis
    paragraphs = re.split(r'\n+', text)
    
    # Look for founding date patterns
    founding_date_patterns = [
        # Year only: "founded in 2010" or "established in 2010"
        r'(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(\d{4})',
        # Month and year: "founded in January 2010"
        r'(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        # Simple year search when company name is directly associated
        r'(?:' + re.escape(company_name) + r')\s+(?:was|were)?\s+(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(\d{4})',
        # Simple founding statement
        r'(?:since|established|founded)\s+in\s+(\d{4})',
    ]
    
    for pattern in founding_date_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches:
                founding_year = matches.group(1)
                history_info['founding_year'] = founding_year
                history_info['founding_context'] = clean_text(para)
                break
        if 'founding_year' in history_info:
            break
    
    # Look for revenue/funding information
    financial_patterns = [
        # Revenue patterns
        r'(?:revenue|sales|turnover)(?:\s+\w+){0,3}\s+(?:of|reached|exceeded|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:\.\d+)?)\s+(?:million|billion|trillion|m|b|t)',
        # Funding patterns
        r'(?:funding|raised|investment|capital|series\s+[a-z])(?:\s+\w+){0,3}\s+(?:of|totaling|totalling|reaching|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:\.\d+)?)\s+(?:million|billion|trillion|m|b|t)',
        # Valuation patterns
        r'(?:valued|valuation|worth|market\s+cap)(?:\s+\w+){0,3}\s+(?:of|at|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:\.\d+)?)\s+(?:million|billion|trillion|m|b|t)',
    ]
    
    for pattern in financial_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'financial_info' not in history_info:
                history_info['financial_info'] = clean_text(para)
                break
    
    # Look for employee count
    employee_patterns = [
        r'(?:employs|employees|team|staff|workforce)(?:\s+\w+){0,3}\s+(?:of|approximately|about|around|nearly|over|more\s+than)?\s+(\d{1,3}(?:,\d{3})*)\s+(?:people|employees|members|professionals|individuals|staff)',
        r'(?:employs|employees|team|staff|workforce|headcount)(?:\s+\w+){0,3}\s+(?:of|approximately|about|around|nearly|over|more\s+than)?\s+(\d{1,3}(?:,\d{3})*)',
    ]
    
    for pattern in employee_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'employee_count' not in history_info:
                history_info['employee_count'] = matches.group(1)
                history_info['employee_context'] = clean_text(para)
                break
    
    # Look for founders information
    founder_patterns = [
        r'(?:founded|established|started|created|began)(?:\s+by\s+)((?:[A-Z][a-z]+ [A-Z][a-z]+)(?:,? (?:and )?))+',
        r'(?:founder|co-founder|creator)(?:s)?\s+(?:is|are|was|were)\s+((?:[A-Z][a-z]+ [A-Z][a-z]+)(?:,? (?:and )?))+',
    ]
    
    for pattern in founder_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'founders' not in history_info:
                history_info['founders'] = matches.group(1).strip()
                history_info['founder_context'] = clean_text(para)
                break
    
    # Look for acquisition information
    acquisition_patterns = [
        r'(?:acquired|purchased|bought|taken\s+over)(?:\s+by\s+)((?:[A-Z][a-z]+ )+)(?:\s+\w+){0,5}\s+in\s+(\d{4})',
        r'(?:acquisition|purchase|takeover|merger)(?:\s+\w+){0,3}\s+by\s+((?:[A-Z][a-z]+ )+)',
    ]
    
    for pattern in acquisition_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'acquisition_info' not in history_info:
                history_info['acquisition_info'] = clean_text(para)
                break
    
    return history_info

def scrape_website(url):
    """Scrape website and extract business information"""
    logger.info(f"Starting scrape of URL: {url}")
    
    try:
        # Parse domain for later use
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc
        
        # Use trafilatura to get clean text
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.error(f"Failed to download URL: {url}")
            return None
        
        # Extract clean text for analysis
        clean_content = trafilatura.extract(downloaded)
        if not clean_content:
            logger.error(f"Failed to extract content from URL: {url}")
            return None
        
        # Use BeautifulSoup for structured parsing
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/123.0.0.0 Safari/537.36'
            )
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='replace')
        
        # Parse with both parsers for better results
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Use our custom HTML parser as well
        parser = MyHTMLParser()
        parser.feed(html_content)
        
        # Extract business information from both methods
        company_name = extract_company_name(soup, domain_name)
        # If company name not found with BeautifulSoup, try the HTML parser
        if company_name == "Unknown Company" and parser.company_name:
            company_name = parser.company_name
        
        # Extract contact information from both visible text and metadata
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_text = ""
        if meta_description and meta_description.has_attr('content'):
            meta_text = meta_description['content']
        
        full_text = f"{clean_content} {meta_text} {str(soup)}"
        
        emails = extract_emails(full_text)
        phones = extract_phones(full_text)
        addresses = extract_addresses(full_text)
        social_media = extract_social_media(full_text)
        
        # Add any contact info from HTML parser
        parsed_contacts = parser.contact_info
        for contact in parsed_contacts:
            # Check for email pattern
            email_match = re.search(EMAIL_PATTERN, contact)
            if email_match:
                emails.append(email_match.group(0))
                continue
                
            # Check for phone pattern
            phone_match = re.search(PHONE_PATTERN, contact)
            if phone_match:
                phones.append(phone_match.group(0))
                continue
                
            # Check for address pattern
            addr_match = re.search(ADDRESS_PATTERN, contact, re.IGNORECASE)
            if addr_match:
                addresses.append(addr_match.group(0))
        
        # Remove duplicates
        emails = list(set(emails))
        phones = list(set(phones))
        addresses = list(set(addresses))
        
        # Extract services and products from clean content and parser
        bs_services, bs_products = extract_services_products(clean_content, company_name)
        
        # Combine services and products from both methods
        services = bs_services
        products = bs_products
        
        # Add services and products from HTML parser
        services.extend([s for s in parser.services if s not in services])
        products.extend([p for p in parser.products if p not in products])
        
        # Limit to top 5 most relevant services and products
        services = services[:5]
        products = products[:5]
        
        # Get meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = []
        if meta_keywords and meta_keywords.has_attr('content'):
            content = meta_keywords['content']
            if content and isinstance(content, str):
                keywords = [k.strip() for k in content.split(',')]
        
        # Get business description
        description = ""
        about_section = soup.find(id=re.compile(r'about', re.I)) or \
                        soup.find('section', class_=re.compile(r'about', re.I)) or \
                        soup.find('div', class_=re.compile(r'about', re.I))
        
        if about_section:
            description = clean_text(about_section.get_text())
        
        if not description and meta_description and meta_description.has_attr('content'):
            description = meta_description['content']
        
        # Extract company history information
        company_history = extract_company_history(clean_content, company_name)
        
        # Combine everything into a result dictionary
        result = {
            'company_name': company_name,
            'description': description[:500] if description else "",
            'contact_info': {
                'emails': emails,
                'phones': phones,
                'addresses': addresses,
                'social_media': social_media
            },
            'services': services,
            'products': products,
            'keywords': keywords,
            'company_history': company_history,
            'url': url,
            'domain': domain_name
        }
        
        logger.info(f"Successfully scraped {url}")
        return result
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return None
