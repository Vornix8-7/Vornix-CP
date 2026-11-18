import os
from flask import Flask
from config import Config
from database import init_app, init_db, migrate_db, init_coach_db
from routes.main import main


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    init_app(app)
    app.register_blueprint(main)

    with app.app_context():
        migrate_db()
        init_coach_db()

    @app.cli.command("init-db")
    def initialize_database():
        init_db()
        print("Database initialized.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
