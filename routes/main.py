import os
import json
import re
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

from extensions import db
from models import Analysis
from services.ai_service import AIService
from config import Config
from utils.validation import is_allowed_file, sanitize_text

main_bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}


@main_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        provider = request.form.get("provider", "gemini")
        jd = sanitize_text(request.form.get("job_description", ""))
        resume_text = sanitize_text(request.form.get("resume_text", ""))

        resume_file = request.files.get("resume_file")
        if resume_file and resume_file.filename:
            filename = secure_filename(resume_file.filename)
            if not is_allowed_file(filename):
                flash("Only PDF and DOCX files are allowed.", "danger")
                return redirect(url_for("main.dashboard"))

            save_path = os.path.join(Config.UPLOAD_FOLDER, f"{current_user.id}_{uuid.uuid4().hex}_{filename}")
            resume_file.save(save_path)
            resume_text = extract_text_from_file(save_path)

        if not resume_text or not jd:
            flash("Resume text and job description are required.", "danger")
            return redirect(url_for("main.dashboard"))

        ai_service = AIService(provider=provider)
        analysis = ai_service.analyze(resume_text, jd)
        if not analysis:
            flash("AI analysis failed. Please check your API key or try again.", "danger")
            return redirect(url_for("main.dashboard"))

        record = Analysis(
            user_id=current_user.id,
            provider=provider,
            ats_score=analysis.get("ats_score", 0),
            job_match=analysis.get("job_match", 0),
            summary=analysis.get("summary", ""),
            skills_found=", ".join(analysis.get("skills_found", [])),
            missing_skills=", ".join(analysis.get("missing_skills", [])),
            strengths=", ".join(analysis.get("strengths", [])),
            weaknesses=", ".join(analysis.get("weaknesses", [])),
            suggestions=", ".join(analysis.get("suggestions", [])),
            recommendation=analysis.get("final_recommendation", "")
        )
        db.session.add(record)
        db.session.commit()
        flash("Analysis completed successfully.", "success")
        return redirect(url_for("main.view_report", analysis_id=record.id))

    return render_template("dashboard.html")


@main_bp.route("/report/<int:analysis_id>")
@login_required
def view_report(analysis_id):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    return render_template("report.html", analysis=analysis)


@main_bp.route("/history")
@login_required
def history():
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template("history.html", analyses=analyses)


@main_bp.route("/delete-report/<int:analysis_id>", methods=["POST"])
@login_required
def delete_report(analysis_id):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    db.session.delete(analysis)
    db.session.commit()
    flash("Report deleted.", "success")
    return redirect(url_for("main.history"))


@main_bp.route("/export-report/<int:analysis_id>")
@login_required
def export_report(analysis_id):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    report_path = generate_pdf_report(analysis)
    return send_file(report_path, as_attachment=True, download_name=f"report_{analysis.id}.pdf")


def extract_text_from_file(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return clean_text(text)
    if ext == ".docx":
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return clean_text("\n".join(paragraphs))
    return ""


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return sanitize_text(text)


def generate_pdf_report(analysis):
    output_path = os.path.join(Config.REPORTS_FOLDER, f"analysis_{analysis.id}.pdf")
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("AI Resume Analyzer Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Provider: {analysis.provider}", styles["Heading2"]))
    story.append(Paragraph(f"ATS Score: {analysis.ats_score}", styles["BodyText"]))
    story.append(Paragraph(f"Job Match: {analysis.job_match}%", styles["BodyText"]))
    story.append(Paragraph(f"Summary: {analysis.summary}", styles["BodyText"]))
    story.append(Paragraph(f"Skills Found: {analysis.skills_found}", styles["BodyText"]))
    story.append(Paragraph(f"Missing Skills: {analysis.missing_skills}", styles["BodyText"]))
    story.append(Paragraph(f"Strengths: {analysis.strengths}", styles["BodyText"]))
    story.append(Paragraph(f"Weaknesses: {analysis.weaknesses}", styles["BodyText"]))
    story.append(Paragraph(f"Suggestions: {analysis.suggestions}", styles["BodyText"]))
    story.append(Paragraph(f"Recommendation: {analysis.recommendation}", styles["BodyText"]))
    doc.build(story)
    return output_path
