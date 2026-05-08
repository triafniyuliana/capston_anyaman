from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import jwt, datetime
from db import get_db_connection
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret123'

bcrypt = Bcrypt(app)

# REGISTER
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request harus JSON"}), 400

    username = data.get("nama")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "Data tidak lengkap"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # cek email
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return jsonify({"message": "Email sudah terdaftar"}), 400

    # hash password
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')

    # insert data
    cursor.execute(
        "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
        (username, email, hashed, "pengguna")
    )
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"message": "Register berhasil"})


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request harus JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email dan password wajib"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Password salah"}), 401

    token = jwt.encode({
        "id": user["id_users"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "message": "Login berhasil",
        "token": token,
        "user": {
            "id": user["id_users"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)