import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as file:
        db.executescript(file.read().decode("utf8"))
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)


def migrate_db():
    db = get_db()

    user_columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(users)").fetchall()
    }

    new_user_columns = {
        "cf_handle": "TEXT",
        "target_rating": "INTEGER NOT NULL DEFAULT 1600",
        "weekly_hours": "INTEGER NOT NULL DEFAULT 7",
        "current_rating": "INTEGER",
        "max_rating": "INTEGER",
        "rating_updated_at": "TEXT"
    }

    for column, definition in new_user_columns.items():
        if column not in user_columns:
            db.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )

    history_columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(rating_history)").fetchall()
    }

    new_history_columns = {
        "contest_id": "INTEGER",
        "rank": "INTEGER",
        "old_rating": "INTEGER",
        "new_rating": "INTEGER"
    }

    for column, definition in new_history_columns.items():
        if column not in history_columns:
            db.execute(
                f"ALTER TABLE rating_history ADD COLUMN {column} {definition}"
            )

    db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_cf_handle
        ON users(cf_handle COLLATE NOCASE)
        WHERE cf_handle IS NOT NULL AND cf_handle != ''
    """)

    db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_rating_contest
        ON rating_history(user_id, contest_id)
        WHERE contest_id IS NOT NULL
    """)

    db.commit()
def init_coach_db():
    db = get_db()

    db.executescript("""
        CREATE TABLE IF NOT EXISTS cf_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            submission_id INTEGER NOT NULL,
            contest_id INTEGER,
            problem_index TEXT,
            problem_name TEXT,
            problem_rating INTEGER,
            tags TEXT,
            verdict TEXT,
            submitted_at INTEGER,
            UNIQUE(user_id, submission_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS coach_sync (
            user_id INTEGER PRIMARY KEY,
            last_sync TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS virtual_contests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            contest_id INTEGER NOT NULL,
            contest_name TEXT NOT NULL,
            started_at INTEGER NOT NULL,
            finished_at INTEGER,
            solved_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    db.commit()
