from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"  # для сесій

def add_message(user_id, message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (user_id, content) VALUES (?,?)', (user_id,message))
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
    SELECT messages.content,
    messages.created_at,
    users.username
    FROM messages
    JOIN users ON messages.user_id = users.id
    ORDER BY messages.created_at DESC""")
    messages = cursor.fetchall()
    conn.close()

    return messages


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
        except:
            return "Користувач вже зареєстрований"

        conn.close()
        return redirect("/login")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/profile")
        else:
            return "Неправильний логін або пароль"

    return render_template('login.html')

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT avatar FROM users WHERE username = ?", (session["user"],))
    image = cursor.fetchone()[0]
    conn.close()

    return render_template("profile.html", image=image, user=session["user"])

@app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():
    if "user" not in session:
        return redirect("/login")
    current_user = session["user"]
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        new_avatar = request.form['avatar']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if new_password:
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET username = ?, password = ?, avatar = ? WHERE username = ?",
                (new_username, hashed_password, new_avatar, current_user)
            )
        else:
            cursor.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                (new_username,current_user)
            )
        conn.commit()
        conn.close()
        session["user"] = new_username
        return redirect("/profile")

    return render_template("edit_profile.html", user=current_user)

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    if "user" not in session:
        return redirect("/login")

    if request.method == 'POST':
        username = session["user"]
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        hashed = cursor.fetchone()
        if not check_password_hash(hashed[0], request.form["password"]):
            return "НЕПРАВИЛЬНИЙ ПАРОЛЬ"

        cursor.execute("DELETE FROM users WHERE username = ?", (username,))

        conn.commit()
        conn.close()

        session.pop("user", None)
        return redirect("/login")

    return render_template("delete.html")

@app.route("/board", methods=['GET', 'POST'])
def board():
    if "user" not in session:
        return redirect("/login")
    user = session["user"]
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
    user_id = cursor.fetchone()[0]

    if request.method == 'POST':
        content = request.form["content"]

        if content.strip():
            add_message(user_id, content)
        return redirect("/board")
    messages = get_messages()
    return render_template("board.html", messages=messages, user=session["user"])

port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)