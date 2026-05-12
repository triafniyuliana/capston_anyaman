from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "secretkey_anyaman"
app.config["UPLOAD_FOLDER"] = "static/uploads"

bcrypt = Bcrypt(app)


# HALAMAN PERTAMA
@app.route("/")
def home():
    return redirect(url_for("login_admin"))


# LOGIN ADMIN
@app.route("/admin/login", methods=["GET", "POST"])
def login_admin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT * FROM users
        WHERE email=%s
        AND role='admin'
        """

        cursor.execute(query, (email,))

        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin and bcrypt.check_password_hash(admin["password"], password):

            session["admin"] = admin["username"]

            return redirect(url_for("dashboard_admin"))

        else:
            flash("Email atau password salah")

    return render_template("admin/login_admin.html")


# REGISTER ADMIN
@app.route("/admin/register", methods=["POST"])
def register_admin():

    data = request.get_json()

    username = data["username"]
    email = data["email"]
    password = data["password"]

    # HASH PASSWORD
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO users(username,email,password,role)
    VALUES(%s,%s,%s,'admin')
    """

    cursor.execute(
        query,
        (username, email, hashed_password)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Admin berhasil ditambahkan"
    })


# DASHBOARD ADMIN
@app.route("/admin/dashboard")
def dashboard_admin():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    return render_template(
        "admin/dashboard_admin.html",
        admin=session["admin"]
    )

# KELOLA PENGGUNA
@app.route("/admin/pengguna")
def kelola_pengguna():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        users.id_users,
        users.username,
        users.email,
        profile_pengguna.nama_lengkap,
        profile_pengguna.no_telepon,
        profile_pengguna.foto_profile,
        profile_pengguna.created_at
    FROM users
    JOIN profile_pengguna
    ON users.id_users = profile_pengguna.id_users
    WHERE users.role='pengguna'
    """

    cursor.execute(query)

    pengguna = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/kelola_pengguna.html",pengguna=pengguna)

# TAMBAH PENGGUNA
@app.route("/admin/pengguna/tambah", methods=["GET", "POST"])
def tambah_pengguna():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        nama_lengkap = request.form["nama_lengkap"]
        no_telepon = request.form["no_telepon"]

        # FOTO
        foto = request.files["foto_profile"]

        filename = secure_filename(foto.filename)

        foto.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

        # HASH PASSWORD
        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()

        # INSERT USERS
        query_users = """
        INSERT INTO users(
            username,
            email,
            password,
            role
        )

        VALUES(%s,%s,%s,'pengguna')
        """

        cursor.execute(
            query_users,
            (
                username,
                email,
                hashed_password
            )
        )

        # AMBIL ID USERS
        id_users = cursor.lastrowid

        # INSERT PROFILE
        query_profile = """
        INSERT INTO profile_pengguna(
            id_users,
            nama_lengkap,
            email,
            no_telepon,
            foto_profile
        )

        VALUES(%s,%s,%s,%s,%s)
        """

        cursor.execute(
            query_profile,
            (
                id_users,
                nama_lengkap,
                email,
                no_telepon,
                filename
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/pengguna")

    return render_template(
        "admin/add_pengguna.html"
    )

# EDIT PENGGUNA
@app.route("/admin/pengguna/edit/<int:id_users>", methods=["GET", "POST"])
def edit_pengguna(id_users):

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET DATA
    query = """
    SELECT
        users.id_users,
        users.username,
        users.email,
        profile_pengguna.nama_lengkap,
        profile_pengguna.no_telepon,
        profile_pengguna.foto_profile
    FROM users
    JOIN profile_pengguna
    ON users.id_users = profile_pengguna.id_users
    WHERE users.id_users=%s
    """

    cursor.execute(query, (id_users,))

    pengguna = cursor.fetchone()

    # UPDATE
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        nama_lengkap = request.form["nama_lengkap"]
        no_telepon = request.form["no_telepon"]
        password = request.form["password"]

        # FOTO
        foto = request.files["foto_profile"]

        if foto.filename != "":

            filename = secure_filename(foto.filename)

            foto.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )

        else:
            filename = pengguna["foto_profile"]

        # UPDATE USERS
        if password != "":

            hashed_password = bcrypt.generate_password_hash(
                password
            ).decode("utf-8")

            query_users = """
            UPDATE users
            SET
                username=%s,
                email=%s,
                password=%s
            WHERE id_users=%s
            """

            cursor.execute(
                query_users,
                (
                    username,
                    email,
                    hashed_password,
                    id_users
                )
            )

        else:

            query_users = """
            UPDATE users
            SET
                username=%s,
                email=%s
            WHERE id_users=%s
            """

            cursor.execute(
                query_users,
                (
                    username,
                    email,
                    id_users
                )
            )

        # UPDATE PROFILE
        query_profile = """
        UPDATE profile_pengguna
        SET
            nama_lengkap=%s,
            email=%s,
            no_telepon=%s,
            foto_profile=%s
        WHERE id_users=%s
        """

        cursor.execute(
            query_profile,
            (
                nama_lengkap,
                email,
                no_telepon,
                filename,
                id_users
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/pengguna")

    cursor.close()
    conn.close()

    return render_template(
        "admin/edit_pengguna.html",
        pengguna=pengguna
    )

# HAPUS PENGGUNA
@app.route("/admin/pengguna/hapus/<int:id_users>")
def hapus_pengguna(id_users):

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # HAPUS PROFILE
    query_profile = """
    DELETE FROM profile_pengguna
    WHERE id_users=%s
    """

    cursor.execute(query_profile, (id_users,))

    # HAPUS USERS
    query_users = """
    DELETE FROM users
    WHERE id_users=%s
    """

    cursor.execute(query_users, (id_users,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin/pengguna")

#KELOLA PENGRAJIN
@app.route("/admin/pengrajin")
def kelola_pengrajin():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        users.id_users,
        users.username,
        users.email,
        profile_pengrajin.nama_lengkap,
        profile_pengrajin.no_telepon,
        profile_pengrajin.pengalaman,
        profile_pengrajin.deskripsi,
        profile_pengrajin.foto_profile,
        profile_pengrajin.alamat,
        profile_pengrajin.created_at
    FROM users
    JOIN profile_pengrajin
    ON users.id_users = profile_pengrajin.id_users
    WHERE users.role='pengrajin'
    """

    cursor.execute(query)

    pengrajin = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/kelola_pengrajin.html",
        pengrajin=pengrajin
    )

# TAMBAH PENGRAJIN
@app.route("/admin/pengrajin/tambah", methods=["GET", "POST"])
def tambah_pengrajin():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        nama_lengkap = request.form["nama_lengkap"]
        no_telepon = request.form["no_telepon"]
        alamat = request.form["alamat"]
        pengalaman = request.form["pengalaman"]
        deskripsi = request.form["deskripsi"]

        # FOTO
        foto = request.files["foto_profile"]

        filename = secure_filename(foto.filename)

        foto.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

        # HASH PASSWORD
        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()

        # INSERT USERS
        query_users = """
        INSERT INTO users(
            username,
            email,
            password,
            role
        )

        VALUES(%s,%s,%s,'pengrajin')
        """

        cursor.execute(
            query_users,
            (
                username,
                email,
                hashed_password
            )
        )

        # AMBIL ID USERS
        id_users = cursor.lastrowid

        # INSERT PROFILE PENGRAJIN
        query_profile = """
        INSERT INTO profile_pengrajin(
            id_users,
            nama_lengkap,
            email,
            no_telepon,
            alamat,
            pengalaman,
            deskripsi,
            foto_profile
        )

        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(
            query_profile,
            (
                id_users,
                nama_lengkap,
                email,
                no_telepon,
                alamat,
                pengalaman,
                deskripsi,
                filename
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/pengrajin")

    return render_template(
        "admin/add_pengrajin.html"
    )

# EDIT PENGRAJIN
@app.route("/admin/pengrajin/edit/<int:id_users>", methods=["GET", "POST"])
def edit_pengrajin(id_users):

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET DATA
    query = """
    SELECT
        users.id_users,
        users.username,
        users.email,
        profile_pengrajin.nama_lengkap,
        profile_pengrajin.no_telepon,
        profile_pengrajin.alamat,
        profile_pengrajin.pengalaman,
        profile_pengrajin.deskripsi,
        profile_pengrajin.foto_profile
    FROM users
    JOIN profile_pengrajin
    ON users.id_users = profile_pengrajin.id_users
    WHERE users.id_users=%s
    """

    cursor.execute(query, (id_users,))

    pengrajin = cursor.fetchone()

    # UPDATE
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        nama_lengkap = request.form["nama_lengkap"]
        no_telepon = request.form["no_telepon"]
        alamat = request.form["alamat"]
        pengalaman = request.form["pengalaman"]
        deskripsi = request.form["deskripsi"]
        password = request.form["password"]

        # FOTO
        foto = request.files["foto_profile"]

        if foto.filename != "":

            filename = secure_filename(foto.filename)

            foto.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )

        else:
            filename = pengrajin["foto_profile"]

        # UPDATE USERS
        if password != "":

            hashed_password = bcrypt.generate_password_hash(
                password
            ).decode("utf-8")

            query_users = """
            UPDATE users
            SET
                username=%s,
                email=%s,
                password=%s
            WHERE id_users=%s
            """

            cursor.execute(
                query_users,
                (
                    username,
                    email,
                    hashed_password,
                    id_users
                )
            )

        else:

            query_users = """
            UPDATE users
            SET
                username=%s,
                email=%s
            WHERE id_users=%s
            """

            cursor.execute(
                query_users,
                (
                    username,
                    email,
                    id_users
                )
            )

        # UPDATE PROFILE
        query_profile = """
        UPDATE profile_pengrajin
        SET
            nama_lengkap=%s,
            email=%s,
            no_telepon=%s,
            alamat=%s,
            pengalaman=%s,
            deskripsi=%s,
            foto_profile=%s
        WHERE id_users=%s
        """

        cursor.execute(
            query_profile,
            (
                nama_lengkap,
                email,
                no_telepon,
                alamat,
                pengalaman,
                deskripsi,
                filename,
                id_users
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/pengrajin")

    cursor.close()
    conn.close()

    return render_template(
        "admin/edit_pengrajin.html",
        pengrajin=pengrajin
    )

# KELOLA VIDEO
@app.route("/admin/video")
def kelola_video():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id_video,
        judul_video,
        kategori,
        deskripsi,
        thumbnail,
        video_file,
        durasi,
        level,
        created_at
    FROM video_tutorial
    ORDER BY id_video DESC
    """

    cursor.execute(query)

    videos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/kelola_video.html",
        videos=videos
    )
# TAMBAH VIDEO
@app.route("/admin/video/tambah", methods=["GET", "POST"])
def tambah_video():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    if request.method == "POST":

        judul_video = request.form["judul_video"]
        kategori = request.form["kategori"]
        deskripsi = request.form["deskripsi"]
        durasi = request.form["durasi"]
        level = request.form["level"]

        # ======================
        # FOLDER VIDEO
        # ======================

        VIDEO_FOLDER = os.path.join(
            app.root_path,
            "static",
            "videos"
        )

        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

        # ======================
        # FOLDER THUMBNAIL
        # ======================

        UPLOAD_FOLDER = os.path.join(
            app.root_path,
            "static",
            "uploads"
        )

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # ======================
        # THUMBNAIL
        # ======================

        thumbnail = request.files["thumbnail"]

        thumbnail_name = secure_filename(
            thumbnail.filename
        )

        thumbnail.save(
            os.path.join(
                UPLOAD_FOLDER,
                thumbnail_name
            )
        )

        # ======================
        # VIDEO
        # ======================

        video = request.files["video_file"]

        video_name = secure_filename(
            video.filename
        )

        video.save(
            os.path.join(
                VIDEO_FOLDER,
                video_name
            )
        )

        # ======================
        # DATABASE
        # ======================

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO video_tutorial(
            judul_video,
            kategori,
            deskripsi,
            thumbnail,
            video_file,
            durasi,
            level
        )

        VALUES(%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                judul_video,
                kategori,
                deskripsi,
                thumbnail_name,
                video_name,
                durasi,
                level
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/video")

    return render_template(
        "admin/add_video.html"
    )

# EDIT VIDEO
@app.route("/admin/video/edit/<int:id_video>", methods=["GET", "POST"])
def edit_video(id_video):

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ======================
    # GET DATA VIDEO
    # ======================

    query = """
    SELECT
        id_video,
        judul_video,
        kategori,
        deskripsi,
        thumbnail,
        video_file,
        durasi,
        level
    FROM video_tutorial
    WHERE id_video=%s
    """

    cursor.execute(query, (id_video,))

    video = cursor.fetchone()

    # ======================
    # UPDATE VIDEO
    # ======================

    if request.method == "POST":

        judul_video = request.form["judul_video"]
        kategori = request.form["kategori"]
        deskripsi = request.form["deskripsi"]
        durasi = request.form["durasi"]
        level = request.form["level"]

        # ======================
        # FOLDER
        # ======================

        VIDEO_FOLDER = os.path.join(
            app.root_path,
            "static",
            "videos"
        )

        UPLOAD_FOLDER = os.path.join(
            app.root_path,
            "static",
            "uploads"
        )

        # ======================
        # THUMBNAIL
        # ======================

        thumbnail = request.files["thumbnail"]

        if thumbnail.filename != "":

            thumbnail_name = secure_filename(
                thumbnail.filename
            )

            thumbnail.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    thumbnail_name
                )
            )

        else:
            thumbnail_name = video["thumbnail"]

        # ======================
        # VIDEO FILE
        # ======================

        video_file = request.files["video_file"]

        if video_file.filename != "":

            video_name = secure_filename(
                video_file.filename
            )

            video_file.save(
                os.path.join(
                    VIDEO_FOLDER,
                    video_name
                )
            )

        else:
            video_name = video["video_file"]

        # ======================
        # UPDATE DATABASE
        # ======================

        query_update = """
        UPDATE video_tutorial
        SET
            judul_video=%s,
            kategori=%s,
            deskripsi=%s,
            thumbnail=%s,
            video_file=%s,
            durasi=%s,
            level=%s
        WHERE id_video=%s
        """

        cursor.execute(
            query_update,
            (
                judul_video,
                kategori,
                deskripsi,
                thumbnail_name,
                video_name,
                durasi,
                level,
                id_video
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/admin/video")

    cursor.close()
    conn.close()

    return render_template(
        "admin/edit_video.html",
        video=video
    )

# HAPUS VIDEO
@app.route("/admin/video/hapus/<int:id_video>")
def hapus_video(id_video):

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET VIDEO
    query = """
    SELECT
        thumbnail,
        video_file
    FROM video_tutorial
    WHERE id_video=%s
    """

    cursor.execute(query, (id_video,))

    video = cursor.fetchone()

    # CEK DATA ADA ATAU TIDAK
    if video is None:

        cursor.close()
        conn.close()

        return redirect("/admin/video")

    # HAPUS THUMBNAIL
    thumbnail_path = os.path.join(
        app.root_path,
        "static",
        "uploads",
        video["thumbnail"]
    )

    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

    # HAPUS VIDEO
    video_path = os.path.join(
        app.root_path,
        "static",
        "videos",
        video["video_file"]
    )

    if os.path.exists(video_path):
        os.remove(video_path)

    # HAPUS DATABASE
    query_delete = """
    DELETE FROM video_tutorial
    WHERE id_video=%s
    """

    cursor.execute(query_delete, (id_video,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin/video")

# KELOLA PRODUK
@app.route("/admin/produk")
def kelola_produk():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        produk.id_produk,
        produk.nama_produk,
        produk.kategori,
        produk.deskripsi,
        produk.harga,
        produk.stok,
        produk.ukuran,
        produk.bahan,
        produk.warna,
        produk.foto_produk,
        produk.whatsapp,
        profile_pengrajin.nama_lengkap
    FROM produk
    JOIN profile_pengrajin
    ON produk.id_pengrajin = profile_pengrajin.id_users
    ORDER BY produk.id_produk DESC
    """

    cursor.execute(query)

    produk = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/kelola_produk.html",
        produk=produk
    )

# KELOLA SERTIFIKAT
@app.route("/admin/sertifikat")
def kelola_sertifikat():

    if "admin" not in session:
        return redirect(url_for("login_admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        sertifikat.id_sertifikat,
        sertifikat.nama_pelatihan,
        sertifikat.nama_pengrajin,
        sertifikat.tanggal_selesai,
        sertifikat.file_sertifikat,
        profile_pengguna.nama_lengkap
    FROM sertifikat
    JOIN profile_pengguna
    ON sertifikat.id_users = profile_pengguna.id_users
    ORDER BY sertifikat.id_sertifikat DESC
    """

    cursor.execute(query)

    sertifikat = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/kelola_sertifikat.html",
        sertifikat=sertifikat
    )

# LOGOUT
@app.route("/admin/logout")
def logout_admin():

    session.pop("admin", None)

    return redirect(url_for("login_admin"))


if __name__ == "__main__":
    app.run(debug=True)