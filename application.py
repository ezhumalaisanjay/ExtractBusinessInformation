
"""
Application Entry Point
"""
from flask import Flask
from main import app as application
import os

# This is required for the application to run properly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port)
