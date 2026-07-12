import json
import logging
import os
import re
import requests
from flask import current_app

from config import Config

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, provider="gemini"):
        self.provider = provider

    def analyze(self, resume_text, job_description):
        if self.provider == "openai":
            return self._analyze_with_openai(resume_text, job_description)
        return self._analyze_with_gemini(resume_text, job_description)

    def _analyze_with_gemini(self, resume_text, job_description):
        api_key = getattr(Config, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logger.error("GEMINI_API_KEY is missing")
            return {"error": "Gemini API key is missing."}
        prompt = self._build_prompt(resume_text, job_description)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_response(content)
        except requests.exceptions.HTTPError as exc:
            detail = self._extract_error_message(response)
            logger.error("Gemini API HTTP error: %s - %s", exc, detail)
            return self._fallback_analysis(resume_text, job_description, detail)
        except Exception as exc:
            logger.exception("Gemini API request failed: %s", exc)
            return self._fallback_analysis(resume_text, job_description, str(exc))

    def _analyze_with_openai(self, resume_text, job_description):
        api_key = getattr(Config, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY is missing")
            return {"error": "OpenAI API key is missing."}
        prompt = self._build_prompt(resume_text, job_description)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": "You analyze resumes and return strict JSON."}, {"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except requests.exceptions.HTTPError as exc:
            detail = self._extract_error_message(response)
            logger.error("OpenAI API HTTP error: %s - %s", exc, detail)
            return self._fallback_analysis(resume_text, job_description, detail)
        except Exception as exc:
            logger.exception("OpenAI API request failed: %s", exc)
            return self._fallback_analysis(resume_text, job_description, str(exc))

    def _fallback_analysis(self, resume_text, job_description, reason=None):
        resume_text = (resume_text or "").lower()
        job_description = (job_description or "").lower()

        known_skills = [
            "python", "java", "javascript", "typescript", "c#", "c++", "php", "sql",
            "html", "css", "react", "node", "flask", "django", "fastapi", "aws",
            "docker", "kubernetes", "git", "linux", "api", "rest", "graphql", "ai",
            "machine learning", "data analysis", "excel", "testing", "automation",
            "communication", "problem solving", "teamwork", "leadership"
        ]

        job_skills = [skill for skill in known_skills if skill in job_description]
        found_skills = [skill for skill in job_skills if skill in resume_text]
        missing_skills = [skill for skill in job_skills if skill not in resume_text]

        if not job_skills:
            job_tokens = set(re.findall(r"[a-z0-9+#.]{2,}", job_description))
            resume_tokens = set(re.findall(r"[a-z0-9+#.]{2,}", resume_text))
            overlap = sorted(job_tokens & resume_tokens)
            found_skills = overlap[:5]
            missing_skills = sorted(job_tokens - resume_tokens)[:5]
        else:
            found_skills = found_skills[:6]
            missing_skills = missing_skills[:6]

        overlap_ratio = len(found_skills) / max(1, len(job_skills) or len(found_skills))
        ats_score = int(min(95, max(45, round(45 + overlap_ratio * 45))))
        job_match = int(min(95, max(40, round(40 + overlap_ratio * 50))))

        summary = "Offline review completed because the AI provider was unavailable or rate-limited."
        if reason:
            summary += f" Reason: {reason}"

        strengths = []
        if found_skills:
            strengths.append(f"Matched relevant keywords: {', '.join(found_skills[:4])}.")
        else:
            strengths.append("Resume appears to contain general experience that may fit the role.")

        weaknesses = []
        if missing_skills:
            weaknesses.append("Some requested skills are not clearly present in the resume.")
        else:
            weaknesses.append("No major skill gaps were detected in the quick review.")

        suggestions = []
        if missing_skills:
            suggestions.append(f"Add evidence for missing skills such as: {', '.join(missing_skills[:4])}.")
        suggestions.append("Mention measurable achievements and relevant tools in the resume.")

        return {
            "ats_score": ats_score,
            "job_match": job_match,
            "summary": summary,
            "skills_found": found_skills,
            "missing_skills": missing_skills,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "final_recommendation": "Proceed with a manual review and tailor the resume to the job description."
        }

    def _build_prompt(self, resume_text, job_description):
        return f"""
Analyze the following resume against the job description and return strict JSON with these keys:
ats_score, job_match, summary, skills_found, missing_skills, strengths, weaknesses, suggestions, final_recommendation.
Use integers for ats_score and job_match. Arrays for list values. Keep values concise.
Resume:
{resume_text}

Job Description:
{job_description}
"""

    def _extract_error_message(self, response):
        if response is None:
            return "No response from provider."
        try:
            payload = response.json()
        except ValueError:
            return response.text[:500] if getattr(response, "text", None) else "Unknown error"

        if isinstance(payload, dict):
            error = payload.get("error", {})
            if isinstance(error, dict):
                message = error.get("message") or error.get("status") or str(error)
                if message:
                    return str(message)
            elif isinstance(error, str):
                return error
        return response.text[:500] if getattr(response, "text", None) else "Unknown error"

    def _parse_response(self, content):
        try:
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned)
            return {
                "ats_score": int(data.get("ats_score", 0)),
                "job_match": int(data.get("job_match", 0)),
                "summary": data.get("summary", ""),
                "skills_found": data.get("skills_found", []),
                "missing_skills": data.get("missing_skills", []),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
                "suggestions": data.get("suggestions", []),
                "final_recommendation": data.get("final_recommendation", "")
            }
        except Exception:
            return {
                "ats_score": 0,
                "job_match": 0,
                "summary": "Unable to parse AI response.",
                "skills_found": [],
                "missing_skills": [],
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "final_recommendation": "Manual review recommended."
            }
