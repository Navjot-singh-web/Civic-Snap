from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import base64
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
def init_db():
    conn = sqlite3.connect('fixmycity.db')
    c = conn.cursor()
    
    # Create issues table
    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_email TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/api/issues', methods=['GET'])
def get_issues():
    conn = sqlite3.connect('fixmycity.db')
    c = conn.cursor()
    
    # Get all issues
    c.execute('SELECT * FROM issues ORDER BY created_at DESC')
    issues = c.fetchall()
    
    # Convert to list of dictionaries
    issue_list = []
    for issue in issues:
        issue_list.append({
            'id': issue[0],
            'category': issue[1],
            'description': issue[2],
            'image_path': issue[3],
            'latitude': issue[4],
            'longitude': issue[5],
            'status': issue[6],
            'created_at': issue[7],
            'user_email': issue[8]
        })
    
    conn.close()
    return jsonify(issue_list)

@app.route('/api/issues', methods=['POST'])
def create_issue():
    data = request.json
    
    # Extract base64 image data
    image_data = data.get('image')
    image_path = None
    
    if image_data:
        # Save image to file system
        image_path = save_image(image_data)
    
    # Save issue to database
    conn = sqlite3.connect('fixmycity.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO issues (category, description, image_path, latitude, longitude, user_email)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('category'),
        data.get('description'),
        image_path,
        data.get('latitude'),
        data.get('longitude'),
        data.get('user_email', 'anonymous@example.com')
    ))
    
    issue_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Send email notification (in a real app, this would be to the appropriate city department)
    send_email_notification(data, issue_id)
    
    return jsonify({'success': True, 'issue_id': issue_id})

def save_image(image_data):
    # Create images directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')
    
    # Generate unique filename
    filename = f"issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join('images', filename)
    
    # Remove data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    # Decode and save image
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(image_data))
    
    return filepath

def send_email_notification(issue_data, issue_id):
    # This is a simplified email function
    # In a real implementation, you would use proper email configuration
    
    # For demo purposes, we'll just print the email content
    email_content = f"""
    New Issue Reported (ID: {issue_id})
    
    Category: {issue_data.get('category')}
    Description: {issue_data.get('description')}
    Location: {issue_data.get('latitude')}, {issue_data.get('longitude')}
    
    Please review and take appropriate action.
    """
    
    print("Email would be sent with content:")
    print(email_content)
    
    # In a real implementation, you would use:
    # smtplib to send the email to the appropriate city department

@app.route('/api/issues/<int:issue_id>/image')
def get_issue_image(issue_id):
    conn = sqlite3.connect('fixmycity.db')
    c = conn.cursor()
    
    c.execute('SELECT image_path FROM issues WHERE id = ?', (issue_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        return send_file(result[0])
    else:
        return jsonify({'error': 'Image not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)