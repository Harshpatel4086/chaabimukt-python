from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import face_recognition
import numpy as np
from PIL import Image
import io
import base64
import json

app = Flask(__name__)
CORS(app)

# Flask route to get all users
@app.route("/get_users", methods=["GET"])
def get_users():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chaabimukt_db"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, device_name FROM users")
    rows = cursor.fetchall()
    users = [
        {"id": row[0], "username": row[1], "device_name": row[2]}
        for row in rows
    ]
    return jsonify(users)

# ✅ Admin: Add new user data
@app.route('/add_user', methods=['POST'])
def add_user():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chaabimukt_db"
    )
    cursor = conn.cursor()


    data = request.get_json()
    username = data.get('username')
    device_name = data.get('device_name')
    image_data = data.get('image')

    if not all([username, device_name, image_data]):
        return jsonify({'error': 'Missing data'}), 400

    try:
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        np_image = np.array(image)

        encodings = face_recognition.face_encodings(np_image)
        if not encodings:
            return jsonify({'error': 'No face found'}), 400

        encoding_str = json.dumps(encodings[0].tolist())

        cursor.execute("""
            INSERT INTO users (username, device_name, face_encoding)
            VALUES (%s, %s, %s)
        """, (username, device_name, encoding_str))
        conn.commit()

        return jsonify({'message': 'User added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ User: Face recognition
@app.route('/recognize', methods=['POST'])
def recognize():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chaabimukt_db"
    )
    cursor = conn.cursor()
    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({'error': 'No image provided'}), 400

    try:
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        np_image = np.array(image)

        unknown_encodings = face_recognition.face_encodings(np_image)
        if not unknown_encodings:
            return jsonify({'result': 'no face found'})

        cursor.execute("SELECT username, device_name, face_encoding FROM users")
        rows = cursor.fetchall()

        for unknown_encoding in unknown_encodings:
            for username, device_name, encoding_str in rows:
                known_encoding = np.array(json.loads(encoding_str))
                result = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.5)
                if result[0]:
                    return jsonify({
                        'result': 'authorized',
                        'username': username,
                        'device_name': device_name
                    })

        return jsonify({'result': 'unauthorized'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_user', methods=['POST'])
def delete_user():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chaabimukt_db"
    )
    cursor = conn.cursor()
    data = request.get_json()
    user_id = data.get("id")

    if not user_id:
        return jsonify({"message": "User ID is required"}), 400

    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"User with ID {user_id} deleted successfully"})
    except Exception as e:
        return jsonify({"message": f"Error deleting user: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
