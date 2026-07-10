from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import User, Analysis
from extensions import db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return render_template("403.html"), 403

    total_users = User.query.count()
    total_analyses = Analysis.query.count()
    missing_skills = []
    for item in Analysis.query.all():
        if item.missing_skills:
            missing_skills.extend([skill.strip() for skill in item.missing_skills.split(",") if skill.strip()])
    from collections import Counter
    common = Counter(missing_skills).most_common(5)
    return render_template("admin.html", total_users=total_users, total_analyses=total_analyses, common_missing_skills=common)
