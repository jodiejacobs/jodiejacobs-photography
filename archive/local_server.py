#!/usr/bin/env python3
"""
Local development server for testing your photography portfolio

This serves your photos locally so you can test the website before deploying.

Usage:
python local_server.py
Then visit: http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the directory containing your website files
    website_dir = Path.cwd()
    os.chdir(website_dir)
    
    print(f"📁 Serving files from: {website_dir}")
    print(f"🌐 Starting server at: http://localhost:{PORT}")
    print("📸 Your photography portfolio will be available at the URL above")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()