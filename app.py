from flask import Flask, render_template, redirect, url_for
import requests
from config import USER_URL, PRIVATE_TOKEN, USER_EMAIL

app = Flask(__name__)
cached_resume = None


def fetch_external_student_info():
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    user_info = {}
    try:
        response = requests.get(USER_URL, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_info["username"] = data.get("username", "не указан")
            user_info["picture"] = data.get("avatar_url", "")
            user_info["name"] = data.get("name", "Не указано")
            user_info["bio"] = data.get("bio", "Нет описания")
            user_id = data.get("id")
            if user_id:

                projects_url = f"https://gitlab.com/api/v4/users/{user_id}/projects"
                response_projects = requests.get(projects_url, headers=headers, timeout=5)
                if response_projects.status_code == 200:
                    projects_data = response_projects.json()
                    user_info["repo_count"] = len(projects_data)
                    user_info["repos"] = [project.get("name", "Unnamed") for project in projects_data]
                else:
                    print("Ошибка получения репозиториев. Статус:", response_projects.status_code)
                    user_info["repo_count"] = "N/A"
                    user_info["repos"] = []
            else:
                user_info["repo_count"] = "N/A"
                user_info["repos"] = []
            return user_info
        else:
            print("Ошибка получения данных с GitLab API. Статус:", response.status_code)
            return {}
    except Exception as e:
        print("Ошибка при обращении к GitLab API:", e)
        return {}


def render_resume_page():
    external_info = fetch_external_student_info()
    context = {
        "username": external_info.get("username", "не указан"),
        "picture": external_info.get("picture", ""),
        "email": USER_EMAIL,
        "repo_count": external_info.get("repo_count", "N/A"),
        "repos": external_info.get("repos", []),
        "name": external_info.get("name", "Не указано"),
        "bio": external_info.get("bio", "Нет описания")
    }
    return render_template("resume.html", **context)


@app.route("/")
def index():
    return cached_resume


@app.route("/update")
def update_resume():
    global cached_resume
    cached_resume = render_resume_page()
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        with app.test_request_context():
            cached_resume = render_resume_page()
    app.run(debug=True, host="0.0.0.0", port=5000)
