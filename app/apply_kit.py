from __future__ import annotations

from app.parser import ParsedCV


def build_apply_kit(cv: ParsedCV, designation: str, location: str, job: dict | None = None) -> dict:
    name = cv.name.split()[0] if cv.name else "I"
    full_name = cv.name or "Candidate"
    years = cv.years_experience
    years_txt = f"{int(years)}+ years" if years and years >= 1 else "hands-on experience"
    skills = ", ".join(cv.skills[:8]) if cv.skills else "the core tools for this role"
    headline = cv.headline or designation
    loc = location or cv.location or "India"
    company = (job or {}).get("company") or "your team"
    job_title = (job or {}).get("title") or designation

    linkedin_post = (
        f"I'm exploring {designation} roles in {loc}.\n\n"
        f"I bring {years_txt} as a {headline}, with strengths in {skills}. "
        f"I care about shipping work that is measurable — not just busy.\n\n"
        f"If you are hiring for {designation} (or know a team that is), I would value a conversation. "
        f"Happy to share work samples.\n\n"
        f"#OpenToWork #{_hashtag(designation)} #Hiring #{_hashtag(loc)}"
    )

    recruiter_note = (
        f"Hi {{Name}}, I came across the {job_title} opening at {company}. "
        f"I am a {headline} with {years_txt} in {skills}. "
        f"I am based in {loc} and would welcome 15 minutes to see if there is a fit. Thank you, {full_name}."
    )

    easy_apply = (
        f"Hello, I am applying for the {job_title} role. "
        f"My background is {headline} ({years_txt}), focused on {skills}. "
        f"I would be glad to discuss how I can contribute at {company}. — {full_name}"
    )

    cover = (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to apply for the {job_title} position"
        + (f" at {company}" if job else "")
        + f". I am a {headline} with {years_txt}, most recently working with {skills}.\n\n"
        f"A few things I would bring to the role:\n"
        f"- Practical delivery in {cv.skills[0] if cv.skills else designation}, not just familiarity\n"
        f"- Clear communication with stakeholders and a bias for finishing work\n"
        f"- A resume you can verify against real outcomes"
        + (f", including {cv.metrics_found[0]}" if cv.metrics_found else "")
        + ".\n\n"
        f"I would welcome the chance to discuss how I can help your team. "
        f"Thank you for your time.\n\n"
        f"Sincerely,\n{full_name}"
        + (f"\n{cv.emails[0]}" if cv.emails else "")
        + (f"\n{cv.phones[0]}" if cv.phones else "")
    )

    email_subjects = [
        f"Application — {job_title} — {full_name}",
        f"{full_name} for {designation} ({loc})",
        f"Re: {job_title} opening",
    ]

    naukri_headline = _naukri_headline(cv, designation, loc)
    linkedin_headline = _linkedin_headline(cv, designation)

    return {
        "designation": designation,
        "linkedin_post": linkedin_post,
        "recruiter_note": recruiter_note,
        "easy_apply": easy_apply,
        "cover_letter": cover,
        "email_subjects": email_subjects,
        "naukri_headline": naukri_headline,
        "linkedin_headline": linkedin_headline,
        "naukri_resume_title": f"{designation} | {skills.split(',')[0].strip() if cv.skills else headline} | {loc}",
    }


def _hashtag(value: str) -> str:
    parts = "".join(ch for ch in value.title() if ch.isalnum())
    return parts[:28] or "Jobs"


def _naukri_headline(cv: ParsedCV, designation: str, loc: str) -> str:
    skills = " | ".join(s.title() if s.islower() else s for s in cv.skills[:4]) or designation
    years = f"{int(cv.years_experience)} Yrs" if cv.years_experience and cv.years_experience >= 1 else "Fresher"
    return f"{designation} | {skills} | {years} | {loc}"[:80]


def _linkedin_headline(cv: ParsedCV, designation: str) -> str:
    skills = " · ".join(cv.skills[:3]) if cv.skills else designation
    return f"{designation} | {skills}"[:120]
