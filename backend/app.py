from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from google.cloud import storage
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', '*****'),
    'user': os.getenv('DB_USER', '*****'),
    'password': os.getenv('DB_PASSWORD', '****'),
    'database': os.getenv('DB_NAME', '****')
}

# GCP Storage configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"*****"
bucket_name = os.getenv('GCP_BUCKET_NAME')
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.json
    name = data['name']
    age = data['age']
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        query = "INSERT INTO users (name, age) VALUES (%s, %s)"
        cursor.execute(query, (name, age))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Data inserted successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/list', methods=['GET'])
def list_data():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users"
        cursor.execute(query)
        
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(results), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        
        file_url = blob.public_url
        
        return jsonify({"message": "File uploaded successfully", "url": file_url}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
