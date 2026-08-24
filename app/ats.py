from __future__ import annotations

import re

from app.parser import ParsedCV
from app.skills import ACTION_VERBS, ROLE_FAMILIES, WEAK_PHRASES


def score_cv(cv: ParsedCV, target_role: str | None = None) -> dict:
    checks: list[dict] = []
    categories: dict[str, dict] = {}

    def add(category: str, label: str, earned: float, max_pts: float, status: str, tip: str):
        checks.append({
            "category": category,
            "label": label,
            "earned": round(earned, 1),
            "max": max_pts,
            "status": status,
            "tip": tip,
        })
        bucket = categories.setdefault(category, {"earned": 0.0, "max": 0.0})
        bucket["earned"] += earned
        bucket["max"] += max_pts

    text_l = cv.text.lower()

    # Parseability 15
    if cv.likely_scanned:
        add("Parseability", "Machine-readable text", 2, 8, "fail",
            "Export a text-based PDF from Word/Google Docs. Image scans fail ATS.")
    elif cv.word_count >= 250:
        add("Parseability", "Machine-readable text", 8, 8, "pass",
            "ATS can extract your content cleanly.")
    else:
        add("Parseability", "Machine-readable text", 5, 8, "warn",
            "Resume is short or sparse. Add impact bullets so parsers have content to index.")

    if 350 <= cv.word_count <= 900:
        add("Parseability", "Resume length", 7, 7, "pass",
            "Length sits in the ATS-friendly 1–2 page range.")
    elif cv.word_count < 350:
        add("Parseability", "Resume length", 3, 7, "warn",
            "Expand experience with quantified bullets. Aim for 400–800 words.")
    else:
        add("Parseability", "Resume length", 4, 7, "warn",
            "Trim older or unrelated roles. Recruiters skim; 1–2 pages is safest.")

    # Contact 12
    add("Contact", "Email", 4 if cv.emails else 0, 4,
        "pass" if cv.emails else "fail",
        "Email found." if cv.emails else "Add a professional email in the header.")
    add("Contact", "Phone", 3 if cv.phones else 0, 3,
        "pass" if cv.phones else "fail",
        "Phone found." if cv.phones else "Add a reachable mobile number with country code.")
    add("Contact", "LinkedIn", 3 if cv.linkedin else 0, 3,
        "pass" if cv.linkedin else "warn",
        "LinkedIn URL found." if cv.linkedin else "Add your LinkedIn profile URL — many Indian ATS forms require it.")
    add("Contact", "Location", 2 if cv.location else 1, 2,
        "pass" if cv.location else "warn",
        f"Location detected: {cv.location}." if cv.location else "Add city + 'Open to relocate/remote' if relevant.")

    # Structure 18
    required = [
        ("experience", "Work experience section"),
        ("education", "Education section"),
        ("skills", "Skills section"),
        ("summary", "Summary / profile"),
    ]
    for key, label in required:
        present = key in cv.sections and len(cv.sections[key]) > 40
        pts = 4.5 if present else (2 if key in cv.sections else 0)
        add("Structure", label, pts, 4.5,
            "pass" if present else "fail",
            "Present and readable." if present else f"Add a clearly labelled '{label.split()[0]}' heading. ATS maps headings, not styling.")

    # Skills 15
    skill_n = len(cv.skills)
    if skill_n >= 10:
        add("Skills", "Keyword coverage", 8, 8, "pass", f"{skill_n} recognised skills indexed.")
    elif skill_n >= 5:
        add("Skills", "Keyword coverage", 5, 8, "warn",
            "Add a dedicated Skills line with tools you actually used (ATS matches exact tokens).")
    else:
        add("Skills", "Keyword coverage", 2, 8, "fail",
            "Too few extractable skills. List tools, languages, and platforms as plain text.")

    family = _family(cv.role_family)
    target = (target_role or cv.headline or "").lower()
    expected = _expected_keywords(family, target)
    missing = [k for k in expected if k not in text_l]
    covered = len(expected) - len(missing)
    if expected:
        ratio = covered / len(expected)
        pts = round(7 * ratio, 1)
        add("Skills", "Role keyword match", pts, 7,
            "pass" if ratio >= 0.7 else "warn" if ratio >= 0.4 else "fail",
            f"Matched {covered}/{len(expected)} expected keywords for this role family.")
    else:
        add("Skills", "Role keyword match", 4, 7, "warn",
            "Set a target job title so we can score keyword fit more precisely.")
        missing = []

    # Experience 20
    has_dates = len(re.findall(r"(20\d{2}|19\d{2})", cv.text)) >= 2
    add("Experience", "Dates on roles", 5 if has_dates else 1, 5,
        "pass" if has_dates else "fail",
        "Year ranges found." if has_dates else "Add start–end years on every role (ATS and recruiters both look for this).")

    verb_hits = sum(1 for v in ACTION_VERBS if re.search(rf"\b{v}\b", text_l))
    if verb_hits >= 6:
        add("Experience", "Action verbs", 6, 6, "pass", f"{verb_hits} strong verbs detected.")
    elif verb_hits >= 3:
        add("Experience", "Action verbs", 3.5, 6, "warn",
            "Start bullets with verbs like Built, Led, Improved, Reduced, Launched.")
    else:
        add("Experience", "Action verbs", 1, 6, "fail",
            "Replace 'Responsible for' with action + outcome (e.g. 'Reduced report time by 40%').")

    metric_n = len(cv.metrics_found)
    if metric_n >= 3:
        add("Experience", "Quantified impact", 9, 9, "pass",
            "Numbers found — ATS and humans both prefer measurable results.")
    elif metric_n >= 1:
        add("Experience", "Quantified impact", 5, 9, "warn",
            "Add more metrics: %, time saved, users, revenue, tickets, SLA.")
    else:
        add("Experience", "Quantified impact", 2, 9, "fail",
            "No numbers detected. Every recent role should include at least one metric.")

    # Professionalism 10
    first_person = len(re.findall(r"\b(i|me|my)\b", text_l))
    add("Professionalism", "Third-person / implied subject", 3 if first_person < 8 else 1, 3,
        "pass" if first_person < 8 else "warn",
        "Voice looks resume-standard." if first_person < 8 else "Drop 'I/my'. Use implied subject: 'Led a 4-person squad…'")

    weak = [p for p in WEAK_PHRASES if p in text_l]
    add("Professionalism", "Cliché language", 4 if not weak else 2, 4,
        "pass" if not weak else "warn",
        "No tired phrases." if not weak else f"Remove: {', '.join(weak[:3])}.")

    bullets = len(re.findall(r"(^|\n)\s*([\-•▪‣*]|\d+\.)\s+", cv.text))
    add("Professionalism", "Bullet formatting", 3 if bullets >= 4 else 1.5, 3,
        "pass" if bullets >= 4 else "warn",
        "Bullet list detected." if bullets >= 4 else "Use simple '-', not text boxes, tables, or icons.")

    earned = round(sum(c["earned"] for c in checks), 1)
    maximum = round(sum(c["max"] for c in checks), 1)
    score = int(round(100 * earned / maximum)) if maximum else 0

    cat_out = []
    for name, vals in categories.items():
        pct = int(round(100 * vals["earned"] / vals["max"])) if vals["max"] else 0
        cat_out.append({
            "name": name,
            "score": pct,
            "earned": round(vals["earned"], 1),
            "max": round(vals["max"], 1),
        })

    suggestions = _suggestions(cv, checks, missing, target_role)
    band = (
        "Excellent — likely to pass most ATS screens"
        if score >= 80
        else "Good — a few targeted edits will lift callbacks"
        if score >= 65
        else "Fair — structure and keywords need work before mass applying"
        if score >= 45
        else "At risk — many ATS parsers will under-index this resume"
    )

    return {
        "score": score,
        "band": band,
        "categories": cat_out,
        "checks": checks,
        "missing_keywords": missing[:12],
        "expected_keywords": expected,
        "suggestions": suggestions,
    }


def _family(key: str | None) -> dict | None:
    for family in ROLE_FAMILIES:
        if family["key"] == key:
            return family
    return None


def _expected_keywords(family: dict | None, target: str) -> list[str]:
    if family:
        return family["keywords"]
    for family in ROLE_FAMILIES:
        if any(t.lower() in target for t in family["titles"]):
            return family["keywords"]
    return []


def _suggestions(cv: ParsedCV, checks: list[dict], missing: list[str], target_role: str | None) -> list[str]:
    tips = []
    fails = [c for c in checks if c["status"] == "fail"]
    warns = [c for c in checks if c["status"] == "warn"]
    for item in fails + warns:
        if item["tip"] not in tips:
            tips.append(item["tip"])
    if missing:
        role = target_role or cv.headline or "your target role"
        tips.append(
            f"Mirror language from {role} JDs. Missing high-value terms: {', '.join(missing[:8])}."
        )
    if "projects" not in cv.sections and len(cv.skills) >= 4:
        tips.append("Add 1–2 projects with stack + outcome if experience is thin.")
    if not cv.github and cv.role_family in {"software_engineer", "data", "devops"}:
        tips.append("Add a GitHub or portfolio URL — engineering ATS forms often have a dedicated field.")
    return tips[:8]
