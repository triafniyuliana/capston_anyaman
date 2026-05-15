import os
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS

import jwt
import datetime

from db import get_db_connection


# BLUEPRINT
api = Blueprint("api", __name__)

# CORS
CORS(api)

# BCRYPT
bcrypt = Bcrypt()

# SECRET KEY
SECRET_KEY = os.getenv("JWT_SECRET_KEY")


# ======================
# REGISTER
# ======================

@api.route(
    "/api/register",
    methods=["POST"]
)

def register():

    data = request.get_json(
        silent=True
    )

    # VALIDASI JSON
    if not data:

        return jsonify({
            "message":
                "Request harus JSON"
        }), 400

    username = data.get("nama")

    email = data.get("email")

    password = data.get("password")

    # VALIDASI INPUT
    if (
        not username or
        not email or
        not password
    ):

        return jsonify({
            "message":
                "Data tidak lengkap"
        }), 400

    # DATABASE
    db = get_db_connection()

    cursor = db.cursor(
        dictionary=True
    )

    # CEK EMAIL
    cursor.execute(

        "SELECT * FROM users WHERE email=%s",

        (email,)
    )

    # EMAIL SUDAH ADA
    if cursor.fetchone():

        cursor.close()

        db.close()

        return jsonify({
            "message":
                "Email sudah terdaftar"
        }), 400

    # HASH PASSWORD
    hashed = (
        bcrypt.generate_password_hash(
            password
        ).decode("utf-8")
    )

    # INSERT USER
    cursor.execute(

        """
        INSERT INTO users
        (
            username,
            email,
            password,
            role
        )

        VALUES(%s,%s,%s,%s)
        """,

        (
            username,
            email,
            hashed,
            "pengguna"
        )
    )

    db.commit()

    cursor.close()

    db.close()

    return jsonify({
        "message":
            "Register berhasil"
    })


# ======================
# LOGIN
# ======================

@api.route(
    "/api/login",
    methods=["POST"]
)

def login():

    data = request.get_json(
        silent=True
    )

    # VALIDASI JSON
    if not data:

        return jsonify({
            "message":
                "Request harus JSON"
        }), 400

    email = data.get("email")

    password = data.get("password")

    # VALIDASI INPUT
    if (
        not email or
        not password
    ):

        return jsonify({
            "message":
                "Email dan password wajib"
        }), 400

    # DATABASE
    db = get_db_connection()

    cursor = db.cursor(
        dictionary=True
    )

    cursor.execute(

        "SELECT * FROM users WHERE email=%s",

        (email,)
    )

    user = cursor.fetchone()

    cursor.close()

    db.close()

    # USER TIDAK ADA
    if not user:

        return jsonify({
            "message":
                "User tidak ditemukan"
        }), 404

    # PASSWORD SALAH
    if not bcrypt.check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "message":
                "Password salah"
        }), 401

    # JWT TOKEN
    token = jwt.encode({

        "id":
            user["id_users"],

        "email":
            user["email"],

        "role":
            user["role"],

        "exp":
            datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(
                hours=2
            )

    },

    SECRET_KEY,

    algorithm="HS256")

    return jsonify({

        "message":
            "Login berhasil",

        "token":
            token,

        "user": {

            "id":
                user["id_users"],

            "username":
                user["username"],

            "email":
                user["email"],

            "role":
                user["role"]
        }
    })