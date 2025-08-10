#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import app

# アプリケーションの起動確認
@app.route('/startup')
def startup_check():
    """アプリケーション起動確認用エンドポイント"""
    return "Application started successfully", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000))) 