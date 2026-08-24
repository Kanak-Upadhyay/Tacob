from __future__ import annotations

import asyncio
import os
import re
from urllib.parse import quote_plus

import httpx

from app.parser import ParsedCV
from app.skills import ROLE_FAMILIES


PORTALS = [
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "builder": lambda role, loc: (
            "https://www.linkedin.com/jobs/search/?keywords="
            f"{quote_plus(role)}&location={quote_plus(loc)}&f_TPR=r2592000"
        ),
    },
    {
        "id": "naukri",
        "name": "Naukri",
        "builder": lambda role, loc: (
            "https://www.naukri.com/"
            f"{_slug(role)}-jobs-in-{_slug(loc)}"
        ),
    },
    {
        "id": "indeed",
        "name": "Indeed",
        "builder": lambda role, loc: (
            f"https://in.indeed.com/jobs?q={quote_plus(role)}&l={quote_plus(loc)}"
        ),
    },
    {
        "id": "foundit",
        "name": "Foundit",
        "builder": lambda role, loc: (
            "https://www.foundit.in/srp/results?"
            f"query={quote_plus(role)}&locations={quote_plus(loc)}"
        ),
    },
    {
        "id": "instahyre",
        "name": "Instahyre",
        "builder": lambda role, loc: f"https://www.instahyre.com/{_slug(role)}-jobs",
    },
    {
        "id": "internshala",
        "name": "Internshala",
        "builder": lambda role, loc: f"https://internshala.com/jobs/{_slug(role)}-job/",
    },
    {
        "id": "shine",
        "name": "Shine",
        "builder": lambda role, loc: (
            f"https://www.shine.com/job-search/{_slug(role)}-jobs-in-{_slug(loc)}"
        ),
    },
]


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "jobs"


def portal_links(role: str, location: str) -> list[dict]:
    loc = location or "India"
    return [
        {"id": p["id"], "name": p["name"], "url": p["builder"](role, loc)}
        for p in PORTALS
    ]


def suggested_designations(cv: ParsedCV, target_role: str | None) -> list[str]:
    titles: list[str] = []
    if target_role:
        titles.append(target_role.strip())
    titles.extend(cv.titles)
    if cv.headline and cv.headline not in titles:
        titles.insert(0, cv.headline)
    family = next((f for f in ROLE_FAMILIES if f["key"] == cv.role_family), None)
    if family:
        titles.extend(family["titles"][:5])
    cleaned: list[str] = []
    seen: set[str] = set()
    for title in titles:
        key = title.lower().strip()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(title.strip())
    return cleaned[:6] or ["Software Engineer"]


def _skill_set(cv: ParsedCV) -> set[str]:
    return {s.lower() for s in cv.skills}


def match_score(cv: ParsedCV, title: str, description: str, location: str, preferred_loc: str) -> int:
    skills = _skill_set(cv)
    blob = f"{title} {description}".lower()
    if not skills:
        skill_pts = 20
    else:
        hits = sum(1 for s in skills if s in blob)
        skill_pts = 70 * min(1.0, hits / max(4, min(len(skills), 10)))
    title_l = title.lower()
    title_pts = 0
    for t in [cv.headline, *cv.titles]:
        if not t:
            continue
        tokens = set(re.findall(r"[a-z]+", t.lower()))
        job_tokens = set(re.findall(r"[a-z]+", title_l))
        if tokens and job_tokens:
            overlap = len(tokens & job_tokens) / len(tokens)
            title_pts = max(title_pts, 25 * overlap)
    loc_pts = 5
    if preferred_loc and preferred_loc.lower() in (location or "").lower():
        loc_pts = 10
    elif "remote" in (location or "").lower():
        loc_pts = 8
    return int(min(99, round(skill_pts + title_pts + loc_pts)))


def search_jobs_sync(cv: ParsedCV, target_role: str | None, location: str) -> dict:
    """Run job search from sync apps such as Streamlit."""
    return _run_async(search_jobs(cv, target_role, location))


def _run_async(coro):
    import concurrent.futures

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def search_jobs(cv: ParsedCV, target_role: str | None, location: str) -> dict:
    designations = suggested_designations(cv, target_role)
    primary = designations[0]
    loc = location or cv.location or "India"

    listings = await _fetch_listings(primary, cv.skills[:8])
    ranked = []
    seen_urls: set[str] = set()
    for job in listings:
        url = job.get("url") or ""
        if url in seen_urls:
            continue
        seen_urls.add(url)
        score = match_score(
            cv,
            job.get("title") or "",
            job.get("description") or "",
            job.get("location") or "",
            loc,
        )
        ranked.append({**job, "match": score})
    ranked.sort(key=lambda j: j["match"], reverse=True)
    if len([j for j in ranked if j["match"] >= 30]) >= 6:
        ranked = [j for j in ranked if j["match"] >= 30]
    else:
        ranked = ranked[:18]

    designation_packs = []
    for title in designations:
        designation_packs.append({
            "title": title,
            "portals": portal_links(title, loc),
        })

    return {
        "query_role": primary,
        "location": loc,
        "designations": designation_packs,
        "jobs": ranked[:24],
        "sources_note": (
            "Live listings come from public job APIs (Arbeitnow, Remotive, The Muse"
            + (", Adzuna" if os.getenv("ADZUNA_APP_ID") else "")
            + "). LinkedIn and Naukri do not offer a public jobs API, so Tacob "
            "opens their official search pages with your role and city pre-filled."
        ),
    }


async def _fetch_listings(role: str, skills: list[str]) -> list[dict]:
    query = role or " ".join(skills[:3]) or "developer"
    timeout = httpx.Timeout(10.0, connect=5.0)
    headers = {"User-Agent": "TacobCV/1.0 (career assistant)"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        results = await asyncio.gather(
            _arbeitnow(client, query),
            _remotive(client, query),
            _muse(client),
            _adzuna(client, query),
            _jobicy(client, query),
            return_exceptions=True,
        )
    jobs: list[dict] = []
    for item in results:
        if isinstance(item, list):
            jobs.extend(item)
    return jobs


async def _arbeitnow(client: httpx.AsyncClient, query: str) -> list[dict]:
    try:
        res = await client.get("https://www.arbeitnow.com/api/job-board-api")
        res.raise_for_status()
        data = res.json().get("data") or []
    except Exception:
        return []
    tokens = [t for t in query.lower().split() if len(t) > 2]
    out = []
    for job in data[:120]:
        title = job.get("title") or ""
        tags = " ".join(job.get("tags") or [])
        blob = f"{title} {tags} {job.get('description') or ''}".lower()
        if tokens and not any(tok in blob for tok in tokens):
            continue
        out.append({
            "title": title,
            "company": job.get("company_name") or "Company",
            "location": job.get("location") or "Remote",
            "url": job.get("url") or "",
            "source": "Arbeitnow",
            "description": re.sub(r"<[^>]+>", " ", job.get("description") or "")[:500],
            "remote": bool(job.get("remote")),
        })
    return out[:15]


async def _remotive(client: httpx.AsyncClient, query: str) -> list[dict]:
    try:
        res = await client.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query, "limit": 20},
        )
        res.raise_for_status()
        jobs = res.json().get("jobs") or []
    except Exception:
        return []
    out = []
    for job in jobs[:15]:
        out.append({
            "title": job.get("title") or "",
            "company": job.get("company_name") or "Company",
            "location": job.get("candidate_required_location") or "Remote",
            "url": job.get("url") or "",
            "source": "Remotive",
            "description": re.sub(r"<[^>]+>", " ", job.get("description") or "")[:500],
            "remote": True,
        })
    return out


async def _muse(client: httpx.AsyncClient) -> list[dict]:
    try:
        res = await client.get(
            "https://www.themuse.com/api/public/jobs",
            params={"page": 0, "descending": "true"},
        )
        res.raise_for_status()
        jobs = res.json().get("results") or []
    except Exception:
        return []
    out = []
    for job in jobs[:12]:
        locs = job.get("locations") or []
        location = locs[0].get("name") if locs else "Remote"
        company = (job.get("company") or {}).get("name") or "Company"
        out.append({
            "title": job.get("name") or "",
            "company": company,
            "location": location,
            "url": (job.get("refs") or {}).get("landing_page") or "",
            "source": "The Muse",
            "description": re.sub(r"<[^>]+>", " ", job.get("contents") or "")[:500],
            "remote": "remote" in location.lower(),
        })
    return out


async def _jobicy(client: httpx.AsyncClient, query: str) -> list[dict]:
    try:
        res = await client.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": 20, "tag": query.split()[0]},
        )
        res.raise_for_status()
        jobs = res.json().get("jobs") or []
    except Exception:
        return []
    out = []
    for job in jobs[:15]:
        out.append({
            "title": job.get("jobTitle") or "",
            "company": job.get("companyName") or "Company",
            "location": job.get("jobGeo") or "Remote",
            "url": job.get("url") or job.get("jobUrl") or "",
            "source": "Jobicy",
            "description": re.sub(r"<[^>]+>", " ", job.get("jobExcerpt") or job.get("jobDescription") or "")[:500],
            "remote": True,
        })
    return out


async def _adzuna(client: httpx.AsyncClient, query: str) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    country = os.getenv("ADZUNA_COUNTRY", "in")
    if not app_id or not app_key:
        return []
    try:
        res = await client.get(
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "results_per_page": 20,
                "content-type": "application/json",
            },
        )
        res.raise_for_status()
        jobs = res.json().get("results") or []
    except Exception:
        return []
    out = []
    for job in jobs:
        loc = (job.get("location") or {}).get("display_name") or "India"
        out.append({
            "title": job.get("title") or "",
            "company": (job.get("company") or {}).get("display_name") or "Company",
            "location": loc,
            "url": job.get("redirect_url") or job.get("adref") or "",
            "source": "Adzuna",
            "description": (job.get("description") or "")[:500],
            "remote": "remote" in loc.lower(),
        })
    return out
