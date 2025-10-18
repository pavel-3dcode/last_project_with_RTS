import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import requests
import uuid
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)


def get_users():
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT uuid, name, bio, skills, avatar FROM portfolio")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_by_uuid(uid):
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE uuid = ?", (uid,))
    user = cursor.fetchone()
    conn.close()
    return user


@app.route("/")
def index():
    info = get_users()
    users = []
    for i in info:
        users.append({
            "uuid": i[0],
            "name": i[1],
            "bio": i[2],
            "skills": [s.strip() for s in i[3].split(",")] if i[3] else [],
            "avatar": i[4]
        })

    filter_skill = request.args.get('skill')
    if filter_skill:
        filter_skill = filter_skill.strip().lower()
        users = [u for u in users if any(filter_skill == s.lower() for s in u["skills"])]

    tool_icons = {
        "Python": "🐍",
        "Flask": "🌶",
        "HTML": "📄",
        "CSS": "🎨",
        "HTML / CSS": "🎭",
        "Git": "📌",
        "Telegram": "✈️",
        "SQL": '🗃',
        "SQLite": "💾",
        "JavaScript": "☕️",
        "JSON": "📦",
        "Jinja": "🧩"
    }


    return render_template('all_portfolios.html', portfolios=users, tool_icons=tool_icons, current_skill=filter_skill)


@app.route("/generate/", methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        form = request.form
        name = form['name']
        bio = form['bio']
        telegram = form['telegram']
        skills = form['skills']
        github = form['github'].strip().replace('https://github.com/', '').replace('/', '')

        uid = str(uuid.uuid4())


        avatar = request.files.get('avatar')
        avatar_filename = None
        if avatar and avatar.filename:
            filename = secure_filename(f"{uid}_{avatar.filename}")
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            avatar_path = os.path.join(upload_folder, filename)
            avatar.save(avatar_path)
            avatar_filename = f"uploads/{filename}"

        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO portfolio (uuid, name, bio, github, telegram, avatar, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, name, bio, github, telegram, avatar_filename, skills))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('form.html')


@app.route('/portfolio/<uid>')
def view_portfolio(uid):
    user = get_user_by_uuid(uid)
    if user is None:
        return "Портфолио не найдено", 404

    user_data = {
        "uuid": user[1],
        "name": user[2],
        "bio": user[3],
        "github": user[4],
        "telegram": user[5],
        "avatar": user[6],
        "skills": [s.strip() for s in user[7].split(",")] if user[7] else []
    }

    tool_icons = {
        "Python": "🐍",
        "Flask": "🌶️",
        "HTML": "📄",
        "CSS": "🎨",
        "HTML / CSS": "🎭",
        "Git": "📌",
        "String": "📝",
        "Telegram": "✈️",
        "Tencipant": "👥",
        "SQL": '🗃',
        "SQLite": "💾",
        "JavaScript": "☕",
        "JSON": "☕",
        "Jinja": "🧩"
    }

    projects = []
    if user_data["github"]:
        url = f"https://api.github.com/users/{user_data['github']}/repos"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                repos = response.json()
                for repo in repos[:6]:
                    projects.append({
                        "title": repo.get("name"),
                        "description": repo.get("description") or "Описание отсутствует",
                        "link": repo.get("html_url")
                    })
        except Exception as e:
            projects.append({"title": "Ошибка", "description": f"GitHub API недоступен: {str(e)}", "link": "#"})

    user_data["projects"] = projects
    print (user_data)
    return render_template("portfolio_template.html", user = user_data, tool_icons = tool_icons)

@app.route('/debug')
def debug():
    users = get_users()
    return {
        'users_count': len(users),
        'users_data': users,
        'columns': ['uuid', 'name', 'bio', 'skills', 'avatar']
    }


if __name__ == "__main__":
    app.run(debug=True)