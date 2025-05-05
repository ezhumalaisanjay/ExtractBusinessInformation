from setuptools import setup, find_packages

setup(
    name='extract-business-info',
    version='0.1.0',
    description='Extract business information from various sources',
    author='Sanjay',
    python_requires='>=3.11',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=True,
    install_requires=[
        'beautifulsoup4>=4.13.4',
        'email-validator>=2.2.0',
        'flask>=3.1.0',
        'flask-sqlalchemy>=3.1.1',
        'gunicorn>=23.0.0',
        'psycopg2-binary>=2.9.10',
        'requests>=2.32.3',
        'trafilatura>=2.0.0',
    ],
)
