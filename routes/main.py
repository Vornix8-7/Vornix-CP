import json
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from urllib.error import URLError
import sqlite3

from database import get_db
from helpers import cf_api

main = Blueprint("main", __name__)


@main.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        handle = request.form.get("cf_handle", "").strip()

        try:
            target = int(request.form.get("target_rating", "1600"))
            hours = int(request.form.get("weekly_hours", "7"))
        except ValueError:
            flash("Enter valid target rating and weekly hours.")
            return redirect(url_for("main.register"))

        if not username or not email or len(password) < 8 or not handle:
            flash("Complete all fields. Password needs at least 8 characters.")
            return redirect(url_for("main.register"))

        if not 800 <= target <= 4000 or not 1 <= hours <= 60:
            flash("Check your target rating and weekly hours.")
            return redirect(url_for("main.register"))

        try:
            profile = cf_api("user.info", {"handles": handle})[0]
        except Exception:
            flash("Codeforces handle not found or API unavailable.")
            return redirect(url_for("main.register"))

        db = get_db()

        try:
            db.execute(
                """
                INSERT INTO users
                (username, email, password_hash, cf_handle,
                 target_rating, weekly_hours, current_rating, max_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    generate_password_hash(password),
                    handle,
                    target,
                    hours,
                    profile.get("rating"),
                    profile.get("maxRating")
                )
            )
            db.commit()
            flash("Account created. Please log in.")
            return redirect(url_for("main.login"))

        except sqlite3.IntegrityError:
            flash("Username, email or Codeforces handle is already registered.")

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


def sync_rating(user):
    if not user["cf_handle"]:
        return

    last_sync = user["rating_updated_at"]
    should_sync = True

    if last_sync:
        try:
            last_time = datetime.fromisoformat(last_sync)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last_time).total_seconds()
            should_sync = age >= 1800
        except ValueError:
            should_sync = True

    if not should_sync:
        return

    db = get_db()

    try:
        profile = cf_api("user.info", {"handles": user["cf_handle"]})[0]
        contests = cf_api("user.rating", {"handle": user["cf_handle"]})

        for contest in contests:
            recorded_at = datetime.fromtimestamp(
                contest["ratingUpdateTimeSeconds"],
                timezone.utc
            ).isoformat()

            db.execute(
                """
                INSERT OR IGNORE INTO rating_history
                (user_id, platform, rating, recorded_at, contest_id,
                 rank, old_rating, new_rating)
                VALUES (?, 'Codeforces', ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    contest["newRating"],
                    recorded_at,
                    contest["contestId"],
                    contest["rank"],
                    contest["oldRating"],
                    contest["newRating"]
                )
            )

        db.execute(
            """
            UPDATE users
            SET current_rating = ?,
                max_rating = ?,
                rating_updated_at = ?
            WHERE id = ?
            """,
            (
                profile.get("rating"),
                profile.get("maxRating"),
                datetime.now(timezone.utc).isoformat(),
                user["id"]
            )
        )

        db.commit()

    except Exception:
        db.rollback()


@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()
    user_id = session["user_id"]

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user:
        session.clear()
        return redirect(url_for("main.login"))

    sync_rating(user)

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    total = db.execute(
        "SELECT COUNT(*) FROM problems WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    solved = db.execute(
        "SELECT COUNT(*) FROM problems WHERE user_id = ? AND status = 'solved'",
        (user_id,)
    ).fetchone()[0]

    pending = db.execute(
        """
        SELECT COUNT(*) FROM problems
        WHERE user_id = ? AND status IN ('todo', 'in_progress')
        """,
        (user_id,)
    ).fetchone()[0]

    history_rows = db.execute(
        """
        SELECT rating, recorded_at
        FROM rating_history
        WHERE user_id = ? AND platform = 'Codeforces'
        ORDER BY recorded_at
        """,
        (user_id,)
    ).fetchall()

    rating_history = [
        {
            "rating": row["rating"],
            "date": row["recorded_at"][:10]
        }
        for row in history_rows
    ]

    return render_template(
        "dashboard.html",
        username=session["username"],
        user=user,
        total=total,
        solved=solved,
        pending=pending,
        rating_history=rating_history
    )


@main.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        handle = request.form.get("cf_handle", "").strip()

        try:
            target = int(request.form.get("target_rating", "1600"))
            hours = int(request.form.get("weekly_hours", "7"))
        except ValueError:
            flash("Enter valid numbers.")
            return redirect(url_for("main.profile"))

        if not handle or not 800 <= target <= 4000 or not 1 <= hours <= 60:
            flash("Check your information.")
            return redirect(url_for("main.profile"))

        try:
            profile_data = cf_api("user.info", {"handles": handle})[0]
        except Exception:
            flash("Codeforces handle not found or API unavailable.")
            return redirect(url_for("main.profile"))

        try:
            db.execute(
                """
                UPDATE users
                SET cf_handle = ?, target_rating = ?, weekly_hours = ?,
                    current_rating = ?, max_rating = ?, rating_updated_at = NULL
                WHERE id = ?
                """,
                (
                    handle,
                    target,
                    hours,
                    profile_data.get("rating"),
                    profile_data.get("maxRating"),
                    user_id
                )
            )
            db.commit()
            flash("Profile updated successfully.")

        except sqlite3.IntegrityError:
            flash("That Codeforces handle is already connected to another account.")

        return redirect(url_for("main.profile"))

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    return render_template("profile.html", user=user)


@main.route("/problems", methods=["GET", "POST"])
def problems():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        platform = request.form.get("platform", "Codeforces").strip()
        external_id = request.form.get("external_id", "").strip()
        url = request.form.get("url", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        status = request.form.get("status", "todo")

        if title and status in ("todo", "in_progress", "solved"):
            try:
                db.execute(
                    """
                    INSERT INTO problems
                    (user_id, title, platform, external_id, url, difficulty, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id, title, platform, external_id or None,
                        url, difficulty or None, status
                    )
                )
                db.commit()
                flash("Problem added.")
            except sqlite3.IntegrityError:
                flash("This problem is already in your collection.")

        return redirect(url_for("main.problems"))

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "")

    query = "SELECT * FROM problems WHERE user_id = ?"
    params = [user_id]

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if status in ("todo", "in_progress", "solved"):
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"

    problem_list = db.execute(query, params).fetchall()

    return render_template(
        "problems.html",
        problems=problem_list,
        search=search,
        selected_status=status
    )


@main.route("/problems/<int:problem_id>/delete", methods=["POST"])
def delete_problem(problem_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()
    db.execute(
        "DELETE FROM problems WHERE id = ? AND user_id = ?",
        (problem_id, session["user_id"])
    )
    db.commit()

    flash("Problem deleted.")
    return redirect(url_for("main.problems"))


@main.route("/find", methods=["GET", "POST"])
def find_problems():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    results = []
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        min_rating = request.form.get("min_rating", "").strip()
        max_rating = request.form.get("max_rating", "").strip()

        try:
            data = cf_api("problemset.problems")
            problems_data = data["problems"]

            for problem in problems_data:
                name = problem.get("name", "")
                rating = problem.get("rating", 0)

                if query and query.lower() not in name.lower():
                    continue

                if min_rating and rating < int(min_rating):
                    continue

                if max_rating and rating > int(max_rating):
                    continue

                contest_id = problem.get("contestId")
                index = problem.get("index", "")
                if not contest_id:
                    continue

                results.append({
                    "name": name,
                    "rating": rating,
                    "contest_id": contest_id,
                    "index": index,
                    "url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
                })

                if len(results) >= 40:
                    break

        except Exception:
            error = "Could not load Codeforces problems. Please try again."

    return render_template("find.html", results=results, error=error)
def sync_coach_submissions(user):
    db = get_db()
    user_id = user["id"]

    sync = db.execute(
        "SELECT last_sync FROM coach_sync WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if sync and sync["last_sync"]:
        try:
            last = datetime.fromisoformat(sync["last_sync"])
            if (datetime.now(timezone.utc) - last).total_seconds() < 21600:
                return
        except ValueError:
            pass

    submissions = cf_api(
        "user.status",
        {"handle": user["cf_handle"], "from": 1, "count": 10000}
    )

    for submission in submissions:
        problem = submission.get("problem", {})
        db.execute(
            """
            INSERT OR REPLACE INTO cf_submissions
            (user_id, submission_id, contest_id, problem_index,
             problem_name, problem_rating, tags, verdict, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                submission["id"],
                problem.get("contestId"),
                problem.get("index"),
                problem.get("name", "Unknown"),
                problem.get("rating"),
                json.dumps(problem.get("tags", [])),
                submission.get("verdict", "UNKNOWN"),
                submission.get("creationTimeSeconds", 0)
            )
        )

    db.execute(
        """
        INSERT OR REPLACE INTO coach_sync (user_id, last_sync)
        VALUES (?, ?)
        """,
        (user_id, datetime.now(timezone.utc).isoformat())
    )

    db.commit()


@main.route("/training")
def training():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user["cf_handle"]:
        flash("Connect your Codeforces account first.")
        return redirect(url_for("main.profile"))

    error = None
    recommendations = []
    stats = {}

    try:
        sync_coach_submissions(user)
    except Exception:
        error = "Could not update submissions. Showing saved analysis."

    submissions = db.execute(
        """
        SELECT * FROM cf_submissions
        WHERE user_id = ?
        ORDER BY submitted_at DESC
        """,
        (user["id"],)
    ).fetchall()

    attempted = {}
    accepted = {}
    solved_ids = set()

    for sub in submissions:
        problem_id = f"{sub['contest_id']}:{sub['problem_index']}"
        tags = json.loads(sub["tags"] or "[]")

        for tag in tags:
            attempted.setdefault(tag, set()).add(problem_id)

            if sub["verdict"] == "OK":
                accepted.setdefault(tag, set()).add(problem_id)

        if sub["verdict"] == "OK":
            solved_ids.add(problem_id)

    for tag in attempted:
        tries = len(attempted[tag])
        solved_count = len(accepted.get(tag, set()))

        stats[tag] = {
            "attempted": tries,
            "solved": solved_count,
            "rate": round(solved_count / tries * 100)
        }

    weak_topics = [
        tag for tag, data in stats.items()
        if data["attempted"] >= 2 and data["rate"] < 60
    ]

    strong_topics = [
        tag for tag, data in stats.items()
        if data["attempted"] >= 2 and data["rate"] >= 75
    ]

    if stats and not weak_topics:
        weak_topics = [
            tag for tag, data in sorted(
                stats.items(),
                key=lambda item: item[1]["rate"]
            )[:3]
        ]

    if weak_topics:
        try:
            problemset = cf_api("problemset.problems")
            problems_data = problemset["problems"]

            current = user["current_rating"] or 1200
            low = max(800, current - 200)
            high = min(4000, current + 300)

            candidates = []

            for problem in problems_data:
                contest_id = problem.get("contestId")
                index = problem.get("index")

                if not contest_id or not index:
                    continue

                problem_id = f"{contest_id}:{index}"
                rating = problem.get("rating")

                if problem_id in solved_ids or not rating:
                    continue

                if not low <= rating <= high:
                    continue

                matching_tags = [
                    tag for tag in problem.get("tags", [])
                    if tag in weak_topics
                ]

                if not matching_tags:
                    continue

                candidates.append({
                    "name": problem["name"],
                    "rating": rating,
                    "tags": problem.get("tags", []),
                    "url": (
                        f"https://codeforces.com/problemset/problem/"
                        f"{contest_id}/{index}"
                    ),
                    "matches": matching_tags
                })

            candidates.sort(
                key=lambda p: (
                    abs(p["rating"] - current),
                    -len(p["matches"])
                )
            )

            recommendations = candidates[:15]

        except Exception:
            error = "Problem recommendations are temporarily unavailable."

    return render_template(
        "training.html",
        stats=stats,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        recommendations=recommendations,
        submission_count=len(submissions),
        error=error
    )
@main.route("/contests")
def contests():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user["cf_handle"]:
        flash("Connect your Codeforces account first.")
        return redirect(url_for("main.profile"))

    recommendations = []
    error = None

    try:
        contest_data = cf_api("contest.list")
        problem_data = cf_api("problemset.problems")["problems"]

        rating = user["current_rating"] or 1200
        averages = {}

        for problem in problem_data:
            contest_id = problem.get("contestId")
            problem_rating = problem.get("rating")

            if contest_id and problem_rating:
                averages.setdefault(contest_id, []).append(problem_rating)

        for contest in contest_data:
            contest_id = contest["id"]

            if contest["phase"] != "FINISHED":
                continue

            ratings = averages.get(contest_id, [])

            if not ratings:
                continue

            average = round(sum(ratings) / len(ratings))

            recommendations.append({
                "id": contest_id,
                "name": contest["name"],
                "average": average,
                "duration": contest["durationSeconds"] // 60,
                "url": f"https://codeforces.com/contest/{contest_id}",
                "difference": abs(average - rating)
            })

        recommendations.sort(key=lambda item: item["difference"])
        recommendations = recommendations[:12]

    except Exception:
        error = "Could not load contests from Codeforces. Try again later."

    active = db.execute(
        """
        SELECT * FROM virtual_contests
        WHERE user_id = ? AND status = 'active'
        ORDER BY started_at DESC
        """,
        (user["id"],)
    ).fetchall()

    history = db.execute(
        """
        SELECT * FROM virtual_contests
        WHERE user_id = ? AND status = 'finished'
        ORDER BY finished_at DESC
        LIMIT 10
        """,
        (user["id"],)
    ).fetchall()

    return render_template(
        "contests.html",
        recommendations=recommendations,
        active=active,
        history=history,
        error=error,
        rating=user["current_rating"] or 1200
    )


@main.route("/contests/start/<int:contest_id>", methods=["POST"])
def start_virtual_contest(contest_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()

    try:
        contest_data = cf_api("contest.list")
        contest = next(
            item for item in contest_data
            if item["id"] == contest_id and item["phase"] == "FINISHED"
        )
    except Exception:
        flash("Could not verify this contest.")
        return redirect(url_for("main.contests"))

    db.execute(
        """
        INSERT INTO virtual_contests
        (user_id, contest_id, contest_name, started_at, status)
        VALUES (?, ?, ?, ?, 'active')
        """,
        (
            session["user_id"],
            contest_id,
            contest["name"],
            int(datetime.now(timezone.utc).timestamp())
        )
    )

    db.commit()

    flash("Virtual contest started. Open the contest on Codeforces.")
    return redirect(url_for("main.contests"))


@main.route("/contests/finish/<int:attempt_id>", methods=["POST"])
def finish_virtual_contest(attempt_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    db = get_db()

    attempt = db.execute(
        """
        SELECT * FROM virtual_contests
        WHERE id = ? AND user_id = ? AND status = 'active'
        """,
        (attempt_id, session["user_id"])
    ).fetchone()

    if not attempt:
        flash("Virtual contest not found.")
        return redirect(url_for("main.contests"))

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    try:
        submissions = cf_api(
            "user.status",
            {"handle": user["cf_handle"], "from": 1, "count": 10000}
        )

        solved = set()

        for submission in submissions:
            if (
                submission.get("contestId") == attempt["contest_id"]
                and submission.get("verdict") == "OK"
                and submission.get("creationTimeSeconds", 0) >= attempt["started_at"]
            ):
                problem = submission.get("problem", {})
                solved.add(problem.get("index"))

        db.execute(
            """
            UPDATE virtual_contests
            SET status = 'finished',
                finished_at = ?,
                solved_count = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                int(datetime.now(timezone.utc).timestamp()),
                len(solved),
                attempt_id,
                session["user_id"]
            )
        )

        db.commit()
        flash(f"Contest finished. You solved {len(solved)} problems.")

    except Exception:
        flash("Could not check your submissions. Please try again.")

    return redirect(url_for("main.contests"))
