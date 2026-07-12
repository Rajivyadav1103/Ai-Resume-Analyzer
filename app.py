import os
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from dotenv import load_dotenv

if not load_dotenv():
    load_dotenv(dotenv_path='.env.example')

from config import Config
from extensions import db, login_manager
from models import User, Analysis
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp
from utils.validation import ensure_directories


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    ensure_directories(app.config["UPLOAD_FOLDER"], app.config["REPORTS_FOLDER"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

        if not User.query.first():
            admin_user = User(username="admin", email="admin@example.com", password_hash="", is_admin=True)
            admin_user.set_password("Admin@123")
            db.session.add(admin_user)
            db.session.commit()

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def handle_404(_):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

