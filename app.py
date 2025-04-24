
import os
import json
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
import face_recognition

app = Flask(__name__)
app.secret_key = os.urandom(24)

users = {
    "user1": "pass1",
    "user2": "pass2",
    "user3": "pass3"
}

known_image_1 = face_recognition.load_image_file("person1.jpg")
known_encoding_1 = face_recognition.face_encodings(known_image_1)[0]

known_image_2 = face_recognition.load_image_file("person2.jpeg")
known_encoding_2 = face_recognition.face_encodings(known_image_2)[0]

known_image_3 = face_recognition.load_image_file("person3.jpeg")
known_encoding_3 = face_recognition.face_encodings(known_image_3)[0]

known_encodings = [known_encoding_1, known_encoding_2, known_encoding_3]
face_recognized = False

def gen_frames():
    global face_recognized
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        rgb_frame = frame[:, :, ::-1]
        encodings = face_recognition.face_encodings(rgb_frame)
        text = "Face Not Recognized"
        color = (0, 0, 255)
        for enc in encodings:
            if any(face_recognition.compare_faces(known_encodings, enc)):
                text = "Face Recognized"
                color = (0, 255, 0)
                face_recognized = True
            else:
                face_recognized = False
        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname in users and users[uname] == pwd:
            session['user'] = uname
            return redirect(url_for('face_recognition_page'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_recognition')
def face_recognition_page():
    return render_template('face_recognition.html', face_recognized=face_recognized)

@app.route('/check_face')
def check_face():
    if face_recognized:
        session['face_recognized'] = True
        return redirect(url_for('generate_card_page'))
    return redirect(url_for('index'))

@app.route('/generate_card_page')
def generate_card_page():
    if session.get('face_recognized'):
        return render_template('generate_card.html')
    return redirect(url_for('index'))

@app.route('/generate_card', methods=['POST'])
def generate_card():
    smart = request.form['smart_card']
    pan = request.form['pan_card']
    aadhar = request.form['aadhar_card']
    user = session.get('user', 'unknown')
    mixed = smart[:4] + pan[-4:] + aadhar[:4] + pan[:4]
    card_data = {
        "user": user,
        "smart_card": smart,
        "pan_card": pan,
        "aadhar_card": aadhar,
        "mixed_card": mixed
    }
    if os.path.exists("cards.json"):
        with open("cards.json", "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(card_data)
    with open("cards.json", "w") as f:
        json.dump(data, f, indent=4)
    session.pop('face_recognized', None)
    return render_template('generated_card.html', mixed_card_number=mixed)

@app.route('/view_cards')
def view_cards():
    if not os.path.exists("cards.json"):
        cards = []
    else:
        with open("cards.json", "r") as f:
            cards = json.load(f)
    return render_template("view_cards.html", cards=cards)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
