from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.apply_kit import build_apply_kit
from app.ats import score_cv
from app.improve import match_job_description, rewrite_cv
from app.jobs import search_jobs
from app.parser import ParsedCV, extract_text_from_upload, parse_cv_text
from app.sample import SAMPLE_RESUME

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

app = FastAPI(title="Tacob", description="CV ATS checker and job matcher")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

MAX_BYTES = 6 * 1024 * 1024


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/analyze")
async def analyze(
    file: UploadFile | None = File(default=None),
    target_role: str = Form(default=""),
    location: str = Form(default=""),
    sample: str = Form(default=""),
):
    try:
        if sample == "1":
            cv = parse_cv_text(SAMPLE_RESUME, filename="sample-resume.txt", sample=True)
        else:
            if not file or not file.filename:
                raise HTTPException(400, "Upload a PDF, DOCX, or TXT resume.")
            data = await file.read()
            if len(data) > MAX_BYTES:
                raise HTTPException(400, "File is larger than 6 MB.")
            text = extract_text_from_upload(file.filename, data)
            cv = parse_cv_text(text, filename=file.filename)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, f"Could not read this file: {exc}") from exc

    role = target_role.strip() or None
    loc = location.strip()
    ats = score_cv(cv, target_role=role)
    jobs = await search_jobs(cv, role, loc)
    designation = jobs["query_role"]
    kit = build_apply_kit(cv, designation, jobs["location"])

    return {
        "cv": cv.to_dict(),
        "ats": ats,
        "jobs": jobs,
        "apply": kit,
    }


@app.post("/api/match-jd")
async def match_jd(
    jd_text: str = Form(...),
    name: str = Form(default="Candidate"),
    headline: str = Form(default=""),
    skills: str = Form(default=""),
    cv_text: str = Form(default=""),
    location: str = Form(default=""),
    years: str = Form(default=""),
    titles: str = Form(default=""),
):
    cv = _cv_from_form(name, headline, skills, cv_text, location, years, titles)
    try:
        return match_job_description(cv, jd_text)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/rewrite")
async def rewrite(
    designation: str = Form(default=""),
    missing: str = Form(default=""),
    name: str = Form(default="Candidate"),
    headline: str = Form(default=""),
    skills: str = Form(default=""),
    cv_text: str = Form(default=""),
    location: str = Form(default=""),
    years: str = Form(default=""),
    metrics: str = Form(default=""),
    experience: str = Form(default=""),
):
    cv = _cv_from_form(name, headline, skills, cv_text, location, years, "", metrics, experience)
    missing_list = [m.strip() for m in missing.split(",") if m.strip()]
    return rewrite_cv(cv, designation or None, missing_list)


@app.post("/api/apply-kit")
async def apply_kit(
    designation: str = Form(...),
    location: str = Form(default="India"),
    name: str = Form(default="Candidate"),
    headline: str = Form(default=""),
    skills: str = Form(default=""),
    years: str = Form(default=""),
    email: str = Form(default=""),
    phone: str = Form(default=""),
    company: str = Form(default=""),
    job_title: str = Form(default=""),
    metrics: str = Form(default=""),
    github: str = Form(default=""),
    role_family: str = Form(default=""),
):
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    years_val = None
    try:
        years_val = float(years) if years else None
    except ValueError:
        years_val = None
    cv = ParsedCV(
        filename="session",
        text="",
        word_count=0,
        name=name,
        emails=[email] if email else [],
        phones=[phone] if phone else [],
        linkedin=None,
        github=github or None,
        location=location,
        headline=headline or designation,
        skills=skill_list,
        sections={},
        titles=[designation],
        years_experience=years_val,
        education=[],
        metrics_found=[m.strip() for m in metrics.split("|") if m.strip()],
        likely_scanned=False,
        role_family=role_family or None,
    )
    job = {"company": company, "title": job_title} if (company or job_title) else None
    return build_apply_kit(cv, designation, location, job)


def _cv_from_form(
    name: str,
    headline: str,
    skills: str,
    cv_text: str = "",
    location: str = "",
    years: str = "",
    titles: str = "",
    metrics: str = "",
    experience: str = "",
) -> ParsedCV:
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    title_list = [t.strip() for t in titles.split(",") if t.strip()]
    years_val = None
    try:
        years_val = float(years) if years else None
    except ValueError:
        years_val = None
    sections = {"experience": experience} if experience else {}
    return ParsedCV(
        filename="session",
        text=cv_text or experience or " ".join(skill_list),
        word_count=len((cv_text or "").split()),
        name=name,
        emails=[],
        phones=[],
        linkedin=None,
        github=None,
        location=location or None,
        headline=headline or None,
        skills=skill_list,
        sections=sections,
        titles=title_list,
        years_experience=years_val,
        education=[],
        metrics_found=[m.strip() for m in metrics.split("|") if m.strip()],
        likely_scanned=False,
        role_family=None,
    )
