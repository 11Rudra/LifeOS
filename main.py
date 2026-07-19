import os
import sqlite3
from pathlib import Path
import html

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / "web" / "templates"))
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("LIFEOS_DB_PATH", str(BASE_DIR / "lifeos.db"))


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS planner_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                category TEXT NOT NULL,
                hours REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(day, category)
            )
            """
        )
        conn.commit()


init_db()


def render_markdown_to_html(content: str) -> str:
    html_parts = []
    in_list = False

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        if stripped.startswith("#"):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            level = len(stripped) - len(stripped.lstrip("#"))
            text = html.escape(stripped[level:].strip())
            html_parts.append(f"<h{level}>{text}</h{level}>")
        elif stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{html.escape(stripped[2:]).strip()}</li>")
        elif "|" in stripped and stripped.count("|") >= 2:
            html_parts.append(f"<p>{html.escape(stripped)}</p>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<p>{html.escape(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


@app.route("/")
def main():
    with sqlite3.connect(DB_PATH) as conn:
        entries = conn.execute(
            "SELECT title, category, content, created_at FROM entries ORDER BY id DESC LIMIT 5"
        ).fetchall()

    model = {
        "title": "LifeOS Command Center",
        "subtitle": "A personal command center for health, family, learning, and growth.",
        "links": [
            ("Command Center", "LifeOS/00-Dashboard.md"),
            ("Learning Roadmap", "LifeOS/01-Learning-Roadmap.md"),
            ("Daily Planner", "LifeOS/templates/daily-planner.md"),
            ("Sunday Review", "LifeOS/templates/sunday-review.md"),
            ("July Metrics", "LifeOS/trackers/metrics-july-2026.md"),
            ("Weekly Planner", "planner"),
        ],
        "entries": [
            {
                "title": title,
                "category": category,
                "content": content,
                "created_at": created_at,
            }
            for title, category, content, created_at in entries
        ],
    }
    return render_template("index.html", model=model)


@app.route("/entries", methods=["GET", "POST"])
def entries():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        content = request.form.get("content", "").strip()

        if title and category and content:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO entries (title, category, content) VALUES (?, ?, ?)",
                    (title, category, content),
                )
                conn.commit()

        return redirect(url_for("main"))

    with sqlite3.connect(DB_PATH) as conn:
        entries_list = conn.execute(
            "SELECT title, category, content, created_at FROM entries ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "entries.html",
        model={
            "title": "LifeOS Entries",
            "entries": [
                {
                    "title": title,
                    "category": category,
                    "content": content,
                    "created_at": created_at,
                }
                for title, category, content, created_at in entries_list
            ],
        },
    )


@app.route("/planner", methods=["GET", "POST"])
def planner():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    tasks = [
        {"name": "Workout", "group": "Health"},
        {"name": "Breakfast & Daughter Learning Session", "group": "Family"},
        {"name": "Deep Work / Coding", "group": "Career"},
        {"name": "Lunch & Walk", "group": "Health"},
        {"name": "Code Reviews / Admin", "group": "Career"},
        {"name": "Family Time", "group": "Family"},
        {"name": "Java / AI Study", "group": "Learning"},
        {"name": "Reading / Tech Study", "group": "Growth"},
        {"name": "Sunday Review", "group": "Reflection"},
    ]
    task_aliases = {
        "Health": "Workout",
        "Family": "Breakfast & Daughter Learning Session",
        "Career": "Deep Work / Coding",
        "Learning": "Java / AI Study",
        "Rest": "Reading / Tech Study",
    }

    if request.method == "POST":
        with sqlite3.connect(DB_PATH) as conn:
            for key, raw_value in request.form.items():
                if not key.startswith("plan-"):
                    continue
                parts = key.split("-", 2)
                if len(parts) != 3:
                    continue
                _, day, task_name = parts
                value = raw_value.strip()
                if not value:
                    continue
                try:
                    hours = float(value)
                except ValueError:
                    continue
                display_task = task_aliases.get(task_name, task_name)
                conn.execute(
                    "INSERT INTO planner_entries (day, category, hours) VALUES (?, ?, ?) ON CONFLICT(day, category) DO UPDATE SET hours=excluded.hours",
                    (day, display_task, hours),
                )
            conn.commit()
        return redirect(url_for("planner"))

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT day, category, hours FROM planner_entries ORDER BY day, category"
        ).fetchall()

    planner_data = {day: {} for day in days}
    for day in days:
        for task in tasks:
            planner_data[day][task["name"]] = ""

    for day, task_name, hours in rows:
        if day in planner_data and task_name in planner_data[day]:
            planner_data[day][task_name] = hours

    return render_template(
        "planner.html",
        model={
            "title": "Weekly Planner",
            "days": days,
            "tasks": tasks,
            "planner_data": planner_data,
        },
    )


@app.route("/<path:filename>")
def render_markdown(filename: str):
    candidate = (BASE_DIR / filename).resolve()
    try:
        candidate.relative_to(BASE_DIR)
    except ValueError:
        return "Not Found", 404

    if not candidate.exists() or not candidate.is_file():
        return "Not Found", 404

    content = candidate.read_text(encoding="utf-8")
    return render_template(
        "markdown_view.html",
        model={"title": candidate.stem.replace("-", " ").title()},
        title=candidate.stem.replace("-", " ").title(),
        content=render_markdown_to_html(content),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)
