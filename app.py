from flask import Flask, request, jsonify, send_from_directory # type: ignore
import face_recognition # type: ignore
import numpy as np # type: ignore
import os
from PIL import Image # type: ignore
import io
import base64
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Load known faces
known_encodings = []
known_names = []

for filename in os.listdir("known_faces"):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join("known_faces", filename)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])

@app.route('/recognize', methods=['POST'])
def recognize_face():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    image_data = base64.b64decode(data['image'].split(',')[1])
    image = Image.open(io.BytesIO(image_data)).convert('RGB')
    image_np = np.array(image)

    unknown_encodings = face_recognition.face_encodings(image_np)

    if not unknown_encodings:
        return jsonify({'result': 'no face found'})

    for face_encoding in unknown_encodings:
        results = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        if True in results:
            matched_name = known_names[results.index(True)]
            return jsonify({'result': 'authorized', 'name': matched_name})

    return jsonify({'result': 'unauthorized'})


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
