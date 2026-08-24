from __future__ import annotations

import re

from app.parser import ParsedCV
from app.skills import ALL_SKILLS, ACTION_VERBS


GENERIC_SKILLS = {
    "inventory", "operations", "leadership", "communication", "training",
    "presentation", "sales", "excel", "word", "ms office",
}


def match_job_description(cv: ParsedCV, jd_text: str) -> dict:
    jd = (jd_text or "").strip()
    if len(jd) < 40:
        raise ValueError("Paste a fuller job description (at least a few lines).")

    jd_l = jd.lower()
    cv_l = cv.text.lower()
    jd_skills = _skills_in(jd_l)
    present = [s for s in jd_skills if s.lower() in cv_l]
    missing = [s for s in jd_skills if s.lower() not in cv_l]

    title_hint = _guess_jd_title(jd)
    title_boost = 0
    if title_hint:
        for t in [cv.headline, *cv.titles]:
            if not t:
                continue
            if t.lower() in title_hint.lower() or title_hint.lower() in t.lower():
                title_boost = 12
                break

    if jd_skills:
        ratio = len(present) / len(jd_skills)
        score = int(min(99, round(100 * ratio * 0.88 + title_boost)))
    else:
        score = 40 + title_boost

    band = (
        "Strong fit — tailor 2–3 bullets and apply"
        if score >= 75
        else "Decent fit — add the missing keywords if they are true"
        if score >= 55
        else "Weak fit — only apply if you can honestly cover the gaps"
    )

    return {
        "score": score,
        "band": band,
        "title_guess": title_hint,
        "jd_skills": jd_skills[:24],
        "present": present[:16],
        "missing": missing[:16],
        "advice": _jd_advice(missing, title_hint),
    }


def rewrite_cv(cv: ParsedCV, designation: str | None = None, missing: list[str] | None = None) -> dict:
    role = designation or cv.headline or "the target role"
    missing = missing or []
    skills = cv.skills[:10]
    years = cv.years_experience
    years_txt = f"{int(years)}+ years" if years and years >= 1 else "proven"
    metric = cv.metrics_found[0] if cv.metrics_found else None

    summary = (
        f"{cv.headline or role} with {years_txt} experience in {', '.join(skills[:5]) or role}. "
        f"Delivers production work with measurable outcomes"
        + (f" (e.g. {metric})" if metric else "")
        + f". Seeking {role} roles where {skills[0] if skills else 'core skills'} and clear delivery matter."
    )

    add_if_true = [m for m in missing if m.lower() not in {s.lower() for s in cv.skills}]
    skills_line = ", ".join(dict.fromkeys([*skills, *add_if_true[:6]]))
    heading = (
        f"{role} | {' | '.join(skills[:4]) or role} | {cv.location or 'India'}"
    )[:80]

    return {
        "improved_summary": summary,
        "skills_line": skills_line,
        "resume_headline": heading,
        "rewritten_bullets": _rewrite_bullets(cv),
        "add_if_true": add_if_true[:8],
        "note": "Only add keywords you have actually used. Inventing skills will fail interviews.",
    }


def _skills_in(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for skill in ALL_SKILLS:
        if skill in GENERIC_SKILLS:
            continue
        pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text) and skill not in seen:
            seen.add(skill)
            found.append(skill)
    return found


def _guess_jd_title(jd: str) -> str | None:
    first = jd.strip().splitlines()[0].strip()
    if 6 < len(first) < 80 and not first.lower().startswith(("job", "about", "we are", "responsib")):
        return first
    match = re.search(r"(?:role|position|title)\s*[:\-]\s*(.+)", jd, re.I)
    if match:
        return match.group(1).strip()[:80]
    return None


def _jd_advice(missing: list[str], title: str | None) -> list[str]:
    tips = []
    if missing:
        tips.append(
            "Mirror these JD terms in Skills and in 1–2 bullets if they are true: "
            + ", ".join(missing[:8]) + "."
        )
    if title:
        tips.append(f"Put '{title}' (or a close variant) near the top of the resume as a headline.")
    tips.append("Keep the file as a text PDF or DOCX. Tables, photos, and icons hide keywords from ATS.")
    return tips[:5]


def _rewrite_bullets(cv: ParsedCV) -> list[dict]:
    experience = cv.sections.get("experience") or cv.text
    raw = []
    for line in experience.splitlines():
        stripped = line.strip()
        if not re.match(r"^([\-•▪‣*]|\d+\.)\s+", stripped):
            continue
        cleaned = re.sub(r"^([\-•▪‣*]|\d+\.)\s+", "", stripped)
        if cleaned:
            raw.append(cleaned)
    out = []
    for line in raw[:8]:
        out.append({"original": line, "improved": _polish_bullet(line)})
    if not out:
        skill = cv.skills[0] if cv.skills else "the core stack"
        out.append({
            "original": "",
            "improved": f"Built production features with {skill} used by stakeholders weekly.",
        })
    return out


def _polish_bullet(line: str) -> str:
    text = line.strip().rstrip(".")
    text = re.sub(r"^(responsible for|duties included|worked on|helped with)\s+", "", text, flags=re.I)
    if text and not any(text.lower().startswith(v) for v in ACTION_VERBS):
        text = "Delivered " + text[0].lower() + text[1:]
    if not re.search(r"\d", text):
        text += " — add a metric (%, time saved, users, tickets) if you have one"
    if text and not text.endswith("."):
        text += "."
    return text[0].upper() + text[1:] if text else text


match_job_description = match_job_description
rewrite_cv = rewrite_cv
