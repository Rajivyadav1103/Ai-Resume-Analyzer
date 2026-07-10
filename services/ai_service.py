import os
import json
import requests
from flask import current_app


class AIService:
    def __init__(self, provider="gemini"):
        self.provider = provider

    def analyze(self, resume_text, job_description):
        if self.provider == "openai":
            return self._analyze_with_openai(resume_text, job_description)
        return self._analyze_with_gemini(resume_text, job_description)

    def _analyze_with_gemini(self, resume_text, job_description):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return None
        prompt = self._build_prompt(resume_text, job_description)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_response(content)
        except Exception:
            return None

    def _analyze_with_openai(self, resume_text, job_description):
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return None
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
        except Exception:
            return None

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
