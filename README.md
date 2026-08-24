# Tacob — CV ATS checker & job matcher

A Streamlit website: upload a resume, get an ATS score, then apply on LinkedIn, Naukri, Indeed, Foundit, Instahyre, and Internshala with copy written for your designation.

## What it does

1. **Upload CV** — PDF, Word (.docx), or text.
2. **Read CV** — Pulls name, contact, skills, titles, education, and metrics.
3. **ATS score** — 100-point checklist: parseability, contact, structure, skills, experience, professionalism.
4. **Match jobs** — Opens official LinkedIn / Naukri / Indeed searches for your role and city. Also ranks live listings from public job APIs (Arbeitnow, Remotive, The Muse). Optional Adzuna key adds more India listings.
5. **Paste a JD** — Score your CV against a LinkedIn or Naukri job description.
6. **Rewrite for ATS** — Get a stronger summary, skills line, and bullet rewrites.
7. **Apply kit** — LinkedIn post, recruiter note, Easy Apply blurb, cover letter, Naukri headline. Use **Write apply** on a live job to tailor the copy.
8. **Download report** — Save the score, keywords, and apply text as a `.txt` file.

LinkedIn and Naukri do not publish a public jobs API. Tacob does **not** scrape those sites. It builds their official search URLs from your CV so you apply on the real portals.

## Run on your computer (one click)

1. Install [Python 3.10+](https://www.python.org/downloads/) if needed. Tick **Add Python to PATH**.
2. Double-click `start.bat`.
3. Your browser should open [http://127.0.0.1:8501](http://127.0.0.1:8501). If it does not, paste that address yourself.

Or in a terminal:

```bat
cd Desktop\Tacob_new\Tacob
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then upload a CV, or click **Try sample resume**.

## Share it as a public website (anyone can open the link)

Deploy on [Streamlit Community Cloud](https://share.streamlit.io) — free, no server to manage.

1. Push this project to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, pick this repo, set the main file to `streamlit_app.py`, and deploy.
4. You get a public URL such as `https://tacob.streamlit.app`. Anyone can open it in one click.

Optional Adzuna keys: in the Streamlit Cloud app, open **Settings → Secrets** and paste the contents of `.streamlit/secrets.toml.example`.

## Optional: more India jobs (Adzuna)

1. Create a free app at [developer.adzuna.com](https://developer.adzuna.com)
2. Copy `.env.example` to `.env` (local) or use Streamlit secrets (cloud)
3. Fill `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`

## Privacy

Files are parsed in memory for the session. Tacob does not save resumes to disk. If you host on Streamlit Cloud, the file is processed on Streamlit’s servers for that session.

## Project layout

```
streamlit_app.py   Website (Streamlit)
app/               CV parser, ATS engine, job matching, apply kit
.streamlit/        Theme and optional secrets
start.bat          One-click run on Windows
requirements.txt
```

The older FastAPI app in `app/main.py` still works if you want an API (`uvicorn app.main:app`). The website people use is Streamlit.
