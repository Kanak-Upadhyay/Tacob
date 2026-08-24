from __future__ import annotations

import html
import os

import streamlit as st
from dotenv import load_dotenv

from app.apply_kit import build_apply_kit
from app.ats import score_cv
from app.improve import match_job_description, rewrite_cv
from app.jobs import search_jobs_sync
from app.parser import ParsedCV, extract_text_from_upload, parse_cv_text
from app.sample import SAMPLE_RESUME

MAX_BYTES = 6 * 1024 * 1024
TABS = ["Overview", "ATS report", "Job matches", "Apply kit", "Read CV"]

st.set_page_config(
    page_title="Tacob — CV ATS & Job Match",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _load_secrets() -> None:
    load_dotenv()
    try:
        for key in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY", "ADZUNA_COUNTRY"):
            value = st.secrets.get(key, "")
            if value:
                os.environ[key] = str(value)
    except Exception:
        pass


_load_secrets()

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Source+Sans+3:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: radial-gradient(1200px 600px at 10% -10%, #f7f1e6, #efe8dc) !important;
  color: #1a2438;
  font-family: "Source Sans 3", system-ui, sans-serif;
}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu,
footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
  display: none !important;
}
[data-testid="stSidebar"] { display: none !important; }
.block-container {
  padding-top: 1.1rem !important;
  padding-bottom: 4rem !important;
  max-width: 1120px !important;
}
.tacob-top { display: flex; justify-content: space-between; align-items: center; margin: 4px 0 22px; }
.brand { display: flex; gap: 12px; align-items: center; }
.mark {
  width: 38px; height: 38px; display: grid; place-items: center;
  background: #1a2438; color: #fffaf2;
  font-family: Fraunces, Georgia, serif; font-weight: 650;
  border-radius: 10px; font-size: 20px;
}
.brand strong { display: block; font-size: 18px; line-height: 1.1; }
.brand small { display: block; font-size: 11px; color: #4a556c; text-transform: uppercase; letter-spacing: 0.16em; }
.tag { color: #4a556c; font-size: 14px; margin: 0; }
.eyebrow { text-transform: uppercase; letter-spacing: 0.18em; font-size: 12px; color: #b4532a; font-weight: 600; margin: 0 0 8px; }
.hero-title {
  font-family: Fraunces, Georgia, serif; font-size: clamp(32px, 4vw, 46px);
  font-weight: 650; line-height: 1.15; color: #1a2438; margin: 0 0 14px;
}
.lede { font-size: 18px; color: #4a556c; margin: 0 0 16px; }
.points { margin: 0; padding: 0; list-style: none; }
.points li { padding: 6px 0 6px 22px; position: relative; }
.points li::before { content: "•"; position: absolute; left: 6px; color: #b4532a; }
.card {
  background: #fffaf2; border: 1px solid #d9cfc0; border-radius: 16px;
  padding: 18px 20px; margin: 0 0 14px; box-shadow: 0 18px 50px rgba(26,36,56,0.06);
}
.score-num { font-family: Fraunces, Georgia, serif; font-size: 72px; font-weight: 650; line-height: 1; color: #b4532a; margin: 6px 0; }
.muted { color: #4a556c; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.chip { background: #efe8dc; border: 1px solid #d9cfc0; border-radius: 999px; padding: 4px 10px; font-size: 13px; }
.badge { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; padding: 3px 8px; border-radius: 999px; flex-shrink: 0; }
.badge.pass { background: #e3f0eb; color: #2c6a5a; }
.badge.warn { background: #f6ead4; color: #b07620; }
.badge.fail { background: #f6e1df; color: #a33b32; }
.check-row { display: flex; gap: 12px; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #efe4d4; }
.portals { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.portals a {
  display: inline-block; background: #1a2438; color: #fffaf2 !important;
  text-decoration: none; padding: 8px 12px; border-radius: 10px; font-size: 13px; font-weight: 600;
}
.job-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.match { font-family: Fraunces, Georgia, serif; font-size: 28px; color: #2c6a5a; font-weight: 650; }
.cat-top { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px; }
.bar { height: 8px; background: #e6ddd0; border-radius: 99px; overflow: hidden; margin-bottom: 10px; }
.bar > span { display: block; height: 100%; background: #b4532a; }
.who small { color: #4a556c; font-weight: 400; }
.pair { border-left: 3px solid #d9cfc0; padding: 8px 0 8px 12px; margin: 10px 0; }
.pair .old { color: #7a8499; text-decoration: line-through; margin: 0 0 4px; }
.cv-text {
  white-space: pre-wrap; font-size: 13px; line-height: 1.55;
  max-height: 520px; overflow: auto; background: #f7f1e6; padding: 14px; border-radius: 12px;
}
.footer-note { text-align: center; color: #4a556c; font-size: 13px; margin-top: 28px; }
div[data-testid="stFileUploader"] section {
  background: #fffaf2; border: 1.5px dashed #c9bba8; border-radius: 16px;
}
.stButton > button { border-radius: 12px !important; font-weight: 600 !important; min-height: 42px; }
.stTextInput input, .stTextArea textarea { background: #fffaf2 !important; border-radius: 10px !important; }
div[role="radiogroup"] label {
  background: #fffaf2; border: 1px solid #d9cfc0; border-radius: 999px; padding: 4px 10px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def init_state() -> None:
    defaults = {
        "analyzed": False,
        "cv": None,
        "ats": None,
        "jobs": None,
        "apply": None,
        "report_tab": "Overview",
        "apply_job": None,
        "jd_result": None,
        "rewrite_result": None,
        "last_missing": [],
        "error": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_report() -> None:
    st.session_state.analyzed = False
    st.session_state.cv = None
    st.session_state.ats = None
    st.session_state.jobs = None
    st.session_state.apply = None
    st.session_state.report_tab = "Overview"
    st.session_state.apply_job = None
    st.session_state.jd_result = None
    st.session_state.rewrite_result = None
    st.session_state.last_missing = []
    st.session_state.error = ""


def run_analysis(cv: ParsedCV, target_role: str, location: str) -> None:
    role = target_role.strip() or None
    loc = location.strip()
    ats = score_cv(cv, target_role=role)
    jobs = search_jobs_sync(cv, role, loc)
    kit = build_apply_kit(cv, jobs["query_role"], jobs["location"])
    st.session_state.cv = cv
    st.session_state.ats = ats
    st.session_state.jobs = jobs
    st.session_state.apply = kit
    st.session_state.analyzed = True
    st.session_state.report_tab = "Overview"
    st.session_state.apply_job = None
    st.session_state.jd_result = None
    st.session_state.rewrite_result = None
    st.session_state.last_missing = ats.get("missing_keywords") or []
    st.session_state.error = ""


def analyze_upload(upload, target_role: str, location: str) -> None:
    if upload is None:
        st.session_state.error = "Choose a resume file, or try the sample."
        return
    data = upload.getvalue()
    if len(data) > MAX_BYTES:
        st.session_state.error = "File is larger than 6 MB."
        return
    try:
        text = extract_text_from_upload(upload.name, data)
        cv = parse_cv_text(text, filename=upload.name)
        run_analysis(cv, target_role, location)
    except ValueError as exc:
        st.session_state.error = str(exc)
    except Exception as exc:
        st.session_state.error = f"Could not read this file: {exc}"


def analyze_sample(target_role: str, location: str) -> None:
    try:
        cv = parse_cv_text(SAMPLE_RESUME, filename="sample-resume.txt", sample=True)
        run_analysis(cv, target_role or "Software Engineer", location or "Bengaluru")
    except Exception as exc:
        st.session_state.error = str(exc)


def report_text() -> str:
    cv: ParsedCV = st.session_state.cv
    ats = st.session_state.ats
    jobs = st.session_state.jobs
    apply = st.session_state.apply
    return "\n".join(
        [
            f"Tacob CV report — {cv.name}",
            f"Headline: {cv.headline or ''}",
            f"ATS score: {ats['score']} ({ats['band']})",
            "",
            "Skills: " + ", ".join(cv.skills or []),
            "",
            "Suggestions:",
            *[f"- {item}" for item in (ats.get("suggestions") or [])],
            "",
            "Apply as: " + jobs["query_role"],
            "LinkedIn headline: " + apply["linkedin_headline"],
            "Naukri headline: " + apply["naukri_headline"],
            "",
            "LinkedIn post:",
            apply["linkedin_post"],
            "",
            "Cover letter:",
            apply["cover_letter"],
        ]
    )


def chips(items: list[str], empty: str = "None") -> str:
    if not items:
        return f'<span class="muted">{esc(empty)}</span>'
    return '<div class="chips">' + "".join(f'<span class="chip">{esc(item)}</span>' for item in items) + "</div>"


def portal_html(portals: list[dict]) -> str:
    return '<div class="portals">' + "".join(
        f'<a href="{esc(portal["url"])}" target="_blank" rel="noopener">{esc(portal["name"])}</a>'
        for portal in portals
    ) + "</div>"


def header() -> None:
    st.markdown(
        """
        <div class="tacob-top">
          <div class="brand">
            <div class="mark">T</div>
            <div><strong>Tacob</strong><small>CV desk</small></div>
          </div>
          <p class="tag">Upload. Score. Match. Apply.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intake() -> None:
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown('<p class="eyebrow">Career desk for India job hunt</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hero-title">Check your CV the way an ATS does — then find where to apply.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="lede">Upload a PDF or Word resume. Tacob reads it, scores ATS fit, '
            "matches live jobs, and writes LinkedIn / Naukri application copy for your designation.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <ul class="points">
              <li>ATS score with a fix-it checklist</li>
              <li>Search LinkedIn, Naukri, Indeed, Foundit</li>
              <li>Ready-to-post apply notes and cover letter</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )

    with right:
        upload = st.file_uploader(
            "Drop your CV here",
            type=["pdf", "docx", "txt", "md"],
            help="PDF, DOCX or TXT · max 6 MB",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            target_role = st.text_input("Target role", placeholder="e.g. Python Developer")
        with col_b:
            location = st.text_input("Location", value="India", placeholder="e.g. Bengaluru")

        btn_a, btn_b = st.columns(2)
        with btn_a:
            check = st.button("Check my CV", type="primary", use_container_width=True)
        with btn_b:
            sample = st.button("Try sample resume", use_container_width=True)

        st.caption(
            "LinkedIn and Naukri listings open on their official sites with your role pre-filled. "
            "Live cards come from public job APIs."
        )

        if check:
            with st.spinner("Reading your CV and scoring ATS fit…"):
                analyze_upload(upload, target_role, location)
            if st.session_state.analyzed:
                st.rerun()
        if sample:
            with st.spinner("Loading sample resume…"):
                analyze_sample(target_role, location)
            if st.session_state.analyzed:
                st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error)


def render_overview(cv: ParsedCV, ats: dict, jobs: dict) -> None:
    c1, c2 = st.columns([0.7, 1.3])
    with c1:
        st.markdown(
            f"""
            <div class="card">
              <div class="muted">ATS score</div>
              <div class="score-num">{ats["score"]}</div>
              <p>{esc(ats["band"])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        bars = ""
        for cat in ats["categories"]:
            bars += (
                f'<div class="cat-top"><span>{esc(cat["name"])}</span><span>{cat["score"]}%</span></div>'
                f'<div class="bar"><span style="width:{cat["score"]}%"></span></div>'
            )
        st.markdown(f'<div class="card">{bars}</div>', unsafe_allow_html=True)

    contact = " · ".join(
        [
            cv.emails[0] if cv.emails else "No email",
            cv.phones[0] if cv.phones else "No phone",
            cv.location or "Location not found",
        ]
    )
    st.markdown(
        f"""
        <div class="card">
          <h3>Read from your CV</h3>
          <p class="muted">{esc(contact)}</p>
          {chips(cv.skills[:16], "No skills extracted")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    tips = "".join(f"<li>{esc(item)}</li>" for item in ats["suggestions"][:5])
    st.markdown(f'<div class="card"><h3>Quick wins</h3><ul>{tips}</ul></div>', unsafe_allow_html=True)

    portals = jobs["designations"][0]["portals"] if jobs["designations"] else []
    st.markdown(
        f"""
        <div class="card">
          <h3>Start applying as {esc(jobs["query_role"])}</h3>
          <p class="muted">{len(jobs["jobs"])} matched listings · search the same role on hiring sites</p>
          {portal_html(portals)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ats(cv: ParsedCV, ats: dict, jobs: dict) -> None:
    rows = ""
    for check in ats["checks"]:
        rows += (
            f'<div class="check-row"><span class="badge {esc(check["status"])}">{esc(check["status"])}</span>'
            f"<div><strong>{esc(check['label'])}</strong>"
            f'<div class="muted">{esc(check["tip"])} · {check["earned"]}/{check["max"]}</div></div></div>'
        )
    st.markdown(
        f"""
        <div class="card">
          <h3>ATS checklist</h3>
          <p class="muted">These are the same signals most parsers and recruiters scan for.</p>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if ats.get("missing_keywords"):
        st.markdown(
            f"""
            <div class="card">
              <h3>Keywords to add if they are true for you</h3>
              {chips(ats["missing_keywords"])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="card">
          <h3>Improve this CV</h3>
          <p class="muted">Rewrite the summary and bullets in an ATS-friendly style. Only keep lines that are true.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Rewrite for ATS", type="primary"):
        missing = st.session_state.last_missing or ats.get("missing_keywords") or []
        st.session_state.rewrite_result = rewrite_cv(cv, jobs.get("query_role"), missing)

    data = st.session_state.rewrite_result
    if data:
        pairs = ""
        for bullet in data.get("rewritten_bullets") or []:
            orig = bullet.get("original") or "(new)"
            pairs += (
                f'<div class="pair"><p class="old">{esc(orig)}</p>'
                f'<p>{esc(bullet["improved"])}</p></div>'
            )
        extra = ""
        if data.get("add_if_true"):
            extra = f'<p class="muted">Add only if true: {esc(", ".join(data["add_if_true"]))}</p>'
        st.markdown(
            f"""
            <div class="card">
              <p><strong>Headline</strong><br>{esc(data["resume_headline"])}</p>
              <p><strong>Summary</strong><br>{esc(data["improved_summary"])}</p>
              <p><strong>Skills line</strong><br>{esc(data["skills_line"])}</p>
              {extra}{pairs}
              <p class="muted">{esc(data.get("note") or "")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_jobs(cv: ParsedCV, jobs: dict) -> None:
    st.markdown(
        """
        <div class="card">
          <h3>Match a pasted job description</h3>
          <p class="muted">Copy a LinkedIn or Naukri JD here to see keyword fit against this CV.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    jd_text = st.text_area(
        "Job description",
        height=140,
        placeholder="Paste the full job description…",
        label_visibility="collapsed",
    )
    if st.button("Score this JD", type="primary"):
        try:
            result = match_job_description(cv, jd_text)
            st.session_state.jd_result = result
            st.session_state.last_missing = result.get("missing") or []
        except ValueError as exc:
            st.warning(str(exc))

    result = st.session_state.jd_result
    if result:
        title = (
            f'<p><strong>Detected role:</strong> {esc(result["title_guess"])}</p>'
            if result.get("title_guess")
            else ""
        )
        advice = "".join(f"<li>{esc(item)}</li>" for item in (result.get("advice") or []))
        st.markdown(
            f"""
            <div class="card">
              <div class="muted">JD match</div>
              <div class="score-num">{result["score"]}</div>
              <p>{esc(result["band"])}</p>
              {title}
              <p><strong>Present</strong></p>
              {chips(result.get("present") or [])}
              <p><strong>Missing</strong></p>
              {chips(result.get("missing") or [])}
              <ul>{advice}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(jobs.get("sources_note") or "")
    st.markdown("### Apply by designation")
    for pack in jobs["designations"]:
        st.markdown(
            f"""
            <div class="card">
              <h3>{esc(pack["title"])}</h3>
              <p class="muted">Open official search results — already filtered for this designation.</p>
              {portal_html(pack["portals"])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Matched live jobs")
    listings = jobs.get("jobs") or []
    if not listings:
        st.info(
            "No live API listings matched right now. Use the LinkedIn and Naukri buttons above — "
            "those searches are built from your CV."
        )
        return

    for i, job in enumerate(listings):
        desc = " ".join((job.get("description") or "").split())[:220]
        st.markdown(
            f"""
            <div class="card">
              <div class="job-head">
                <div>
                  <h3>{esc(job.get("title"))}</h3>
                  <div class="muted">{esc(job.get("company"))} · {esc(job.get("location"))} · {esc(job.get("source"))}</div>
                  <p class="muted">{esc(desc)}{"…" if desc else ""}</p>
                </div>
                <div class="match">{job.get("match", 0)}%</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([0.2, 0.22, 0.58])
        with b1:
            st.link_button("View", job.get("url") or "#", use_container_width=True)
        with b2:
            if st.button("Write apply", key=f"apply_{i}", use_container_width=True):
                st.session_state.apply_job = job
                st.session_state.apply = build_apply_kit(
                    cv,
                    job.get("title") or jobs["query_role"],
                    jobs.get("location") or "India",
                    {"company": job.get("company"), "title": job.get("title")},
                )
                st.session_state.report_tab = "Apply kit"
                st.rerun()


def render_apply(cv: ParsedCV, jobs: dict, apply: dict) -> None:
    titles = [pack["title"] for pack in jobs.get("designations") or []]
    if not titles:
        titles = [jobs.get("query_role") or "Software Engineer"]

    current_job = st.session_state.apply_job
    default = (current_job or {}).get("title") if current_job else apply.get("designation")
    index = titles.index(default) if default in titles else 0
    picked = st.selectbox("Job title to apply for", titles, index=index)

    if picked != apply.get("designation") and not current_job:
        st.session_state.apply = build_apply_kit(cv, picked, jobs.get("location") or "India")
        apply = st.session_state.apply

    if current_job:
        st.caption(f"Tailored for {current_job.get('title')} at {current_job.get('company')}.")
        if st.button("Clear job tailoring"):
            st.session_state.apply_job = None
            st.session_state.apply = build_apply_kit(cv, picked, jobs.get("location") or "India")
            st.rerun()

    apply = st.session_state.apply
    st.markdown(
        f"""
        <div class="card">
          <h3>Profile titles</h3>
          <p><strong>LinkedIn headline</strong><br>{esc(apply["linkedin_headline"])}</p>
          <p><strong>Naukri headline</strong><br>{esc(apply["naukri_headline"])}</p>
          <p><strong>Naukri resume title</strong><br>{esc(apply["naukri_resume_title"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    blocks = [
        ("LinkedIn post", apply["linkedin_post"]),
        ("Recruiter / hiring-manager note", apply["recruiter_note"]),
        ("Easy Apply message", apply["easy_apply"]),
        ("Cover letter", apply["cover_letter"]),
    ]
    for title, text in blocks:
        st.markdown(f'<div class="card"><h3>{esc(title)}</h3></div>', unsafe_allow_html=True)
        st.text_area(title, value=text, height=180, label_visibility="collapsed", key=f"kit_{title}")

    subjects = "".join(f"<li>{esc(item)}</li>" for item in apply.get("email_subjects") or [])
    st.markdown(
        f'<div class="card"><h3>Email subjects</h3><ul>{subjects}</ul></div>',
        unsafe_allow_html=True,
    )


def render_read(cv: ParsedCV) -> None:
    st.markdown(
        f"""
        <div class="card">
          <h3>Extracted CV text</h3>
          <p class="muted">This is what an ATS is likely to read. If this looks messy, export a simpler PDF from Word.</p>
          <div class="cv-text">{esc(cv.text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_report() -> None:
    cv: ParsedCV = st.session_state.cv
    ats = st.session_state.ats
    jobs = st.session_state.jobs
    apply = st.session_state.apply

    bar1, bar2, bar3 = st.columns([0.22, 1, 0.28])
    with bar1:
        if st.button("← New CV", use_container_width=True):
            reset_report()
            st.rerun()
    with bar2:
        st.markdown(
            f'<div class="who"><strong>{esc(cv.name)}</strong> '
            f'<small>{esc(cv.headline or "Resume")} · {cv.word_count} words</small></div>',
            unsafe_allow_html=True,
        )
    with bar3:
        st.download_button(
            "Download report",
            data=report_text(),
            file_name=f"{cv.name or 'tacob'}-cv-report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    picked = st.radio(
        "Section",
        TABS,
        horizontal=True,
        label_visibility="collapsed",
        key="report_tab",
    )

    if picked == "Overview":
        render_overview(cv, ats, jobs)
    elif picked == "ATS report":
        render_ats(cv, ats, jobs)
    elif picked == "Job matches":
        render_jobs(cv, jobs)
    elif picked == "Apply kit":
        render_apply(cv, jobs, apply)
    else:
        render_read(cv)


def main() -> None:
    init_state()
    header()
    if st.session_state.analyzed and st.session_state.cv:
        render_report()
    else:
        render_intake()
    st.markdown(
        '<p class="footer-note">Tacob processes resumes in memory for this session and does not save files to disk.</p>',
        unsafe_allow_html=True,
    )


main()
