from setuptools import setup, find_packages

setup(
    name="linkedin-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.13.4",
        "email-validator>=2.2.0",
        "flask>=3.1.0",
        "flask-sqlalchemy>=3.1.1",
        "gunicorn>=23.0.0",
        "psycopg2-binary>=2.9.10",
        "requests>=2.32.3",
        "trafilatura>=2.0.0",
        "lxml>=4.9.2",
        "urllib3>=1.26.15",
        "Werkzeug>=2.2.3",
    ],
    python_requires=">=3.11",
)