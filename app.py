from flask import (
    Flask, request, render_template,
    abort, make_response, send_from_directory, send_file
)
import sqlite3
import markdown
import os

app = Flask(__name__)

# ======================
# DATABASE
# ======================

def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)
    cur.execute(
        "INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'admin123')"
    )
    conn.commit()
    conn.close()

init_db()

# ======================
# INDEX
# ======================

@app.route("/")
def index():
    return render_template("index.html")

# ======================
# MARKDOWN DOCS
# ======================

@app.route("/docs/<vuln>")
def docs(vuln):
    path = f"static/md/{vuln}.md"

    if not os.path.exists(path):
        abort(404)

    with open(path, encoding="utf-8") as f:
        md_text = f.read()

    html = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables"]
    )

    return render_template(
        "docs.html",
        content=html,
        title=vuln.upper()
    )

@app.route("/sources")
def sources():
    return render_template("sources.html")


# ======================
# SQL INJECTION
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    result = None
    query = None
    success = False

    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")

        query = f"SELECT * FROM users WHERE username='{user}' AND password='{pwd}';"

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute(query)
            result = cur.fetchone()
            success = bool(result)
        except Exception as e:
            result = str(e)
        conn.close()

    return render_template(
        "login.html",
        success=success,
        query=query
    )

# ======================
# XSS
# ======================

@app.route("/xss", methods=["GET", "POST"])
def xss():
    comment = None
    if request.method == "POST":
        comment = request.form.get("comment", "")
    return render_template("xss.html", comment=comment)

# ======================
# DIRECTORY TRAVERSAL
# ======================

@app.route("/traversal")
def traversal():
    base_dir = "safe_files/"
    filename = request.args.get("file")

    if not filename:
        return render_template("traversal.html")

    filepath = os.path.join(base_dir, filename)

    if not os.path.exists(filepath):
        return render_template("traversal.html", error="Файл не найден")

    if filepath.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        return send_file(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return render_template(
            "traversal.html",
            content=content,
            filename=filename
        )
    except Exception as e:
        return render_template("traversal.html", error=str(e))

# ======================
# FILE UPLOAD
# ======================

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    message = None
    filename = None

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            message = f"Файл загружен: {filename}"

    return render_template("upload.html", message=message, filename=filename)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ======================
# COOKIE TAMPERING
# ======================

@app.route("/cookies")
def cookies_demo():
    role = request.cookies.get("role", "user")

    if role == "admin":
        text = "Вы администратор! Доступ открыт."
    else:
        text = "Обычный пользователь. Попробуйте изменить cookie role."

    resp = make_response(
        render_template("cookies.html", role=role, text=text)
    )
    resp.set_cookie("role", role)
    return resp

# ======================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
