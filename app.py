from flask import Flask, request, render_template
import sqlite3

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
            return f"<h3>Неверный логин/пароль</h3>"

    return render_template("login.html")

@app.route("/xss", methods=["GET", "POST"])
def xss():
    message = ""
    if request.method == "POST":
        message = request.form.get("message", "")
    return render_template("xss.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)
