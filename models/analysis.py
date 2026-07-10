from datetime import datetime
from extensions import db


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    ats_score = db.Column(db.Integer, nullable=False)
    job_match = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    skills_found = db.Column(db.Text, nullable=True)
    missing_skills = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
