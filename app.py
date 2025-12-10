from flask import Flask, request, render_template
from flask import make_response
from flask import send_from_directory
import sqlite3

import os

app = Flask(__name__)

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
    cur.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'admin123')")
    conn.commit()
    conn.close()

init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")

        # ⚠ УЯЗВИМЫЙ SQL (только для учебного полигона)
        query = f"SELECT * FROM users WHERE username='{user}' AND password='{pwd}';"

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute(query)
            result = cur.fetchone()
        except Exception as e:
            result = None
            return f"<b>SQL Error:</b><br>{e}<br><br><b>Query:</b><br>{query}"

        conn.close()

        if result:
            return f"<h3>Вход успешен!</h3><p>Добро пожаловать, {user}</p><br>Таков запрос:<br><code>{query}</code>"
        else:
            return f"<h3>Неверный логин/пароль</h3></p><br>Таков запрос:<br><code>{query}</code>"

    return render_template("login.html")

@app.route("/xss", methods=["GET", "POST"])
def xss():
    message = ""
    if request.method == "POST":
        message = request.form.get("message", "")
    return render_template("xss.html", message=message)



@app.route("/traversal", methods=["GET"])
def traversal():
    filename = request.args.get("file", "").strip()

    if not filename:
        return render_template("traversal.html", filename=None, content=None)

    try:
        # Безопасный путь для демонстрации (не разрешаем абсолютные пути)
        # Но для учебной демострации мы разрешаем относительные traversal-пути.
        # Попробуем открыть в текстовом режиме с fallback'ом.
        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            # fallback: откроем в бинарном виде и отобразим первые 2000 байт в hex+repr
            with open(filename, "rb") as f:
                raw = f.read(2000)
                content = ("(binary or non-utf8 file, showing first bytes)\n\n"
                           + repr(raw))
    except Exception as e:
        content = f"Ошибка: {e}"

    return render_template("traversal.html", filename=filename, content=content)


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    message = None
    filename = None
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            # Сохраняем файл как есть (для учебного полигона)
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            message = f"Файл сохранён: {filename}"
    return render_template("upload.html", message=message, filename=filename)

# Маршрут для отдачи загруженных файлов
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # Отдаём файл из папки uploads
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/cookies")
def cookies_demo():
    role = request.cookies.get("role")

    if not role:
        role = "user"

    if role == "admin":
        text = "Вы администратор! Вам доступна секретная информация."
    else:
        text = "Статус: обычный пользователь. Попробуйте изменить куки!"

    resp = make_response(render_template("cookies.html", role=role, text=text))
    resp.set_cookie("role", role)  # важно!
    return resp


if __name__ == "__main__":
    app.run(debug=True)
