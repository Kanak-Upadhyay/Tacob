const state = { data: null };

const $ = (id) => document.getElementById(id);
const intake = $("intake");
const working = $("working");
const report = $("report");
const form = $("upload-form");
const drop = $("drop");
const fileInput = $("file");
const fileName = $("file-name");

drop.addEventListener("click", () => fileInput.click());
drop.addEventListener("dragover", (e) => {
  e.preventDefault();
  drop.classList.add("over");
});
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  if (e.dataTransfer.files[0]) {
    fileInput.files = e.dataTransfer.files;
    fileName.textContent = e.dataTransfer.files[0].name;
  }
});
fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0] ? fileInput.files[0].name : "No file chosen";
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files[0]) {
    alert("Choose a resume file, or try the sample.");
    return;
  }
  const fd = new FormData();
  fd.append("file", fileInput.files[0]);
  fd.append("target_role", $("target_role").value);
  fd.append("location", $("location").value);
  await runAnalyze(fd, "Reading your CV and scoring ATS fit…");
});

$("sample-btn").addEventListener("click", async () => {
  const fd = new FormData();
  fd.append("sample", "1");
  fd.append("target_role", $("target_role").value || "Software Engineer");
  fd.append("location", $("location").value || "Bengaluru");
  await runAnalyze(fd, "Loading sample resume…");
});

$("reset-btn").addEventListener("click", () => {
  report.classList.add("hidden");
  intake.classList.remove("hidden");
  fileInput.value = "";
  fileName.textContent = "No file chosen";
});

$("download-btn").addEventListener("click", downloadReport);

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("on"));
    btn.classList.add("on");
    ["overview", "ats", "jobs", "apply", "read"].forEach((name) => {
      $("panel-" + name).classList.toggle("hidden", btn.dataset.tab !== name);
    });
  });
});

async function runAnalyze(fd, msg) {
  intake.classList.add("hidden");
  report.classList.add("hidden");
  working.classList.remove("hidden");
  $("working-msg").textContent = msg;
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Analyze failed");
    state.data = data;
    renderAll(data);
    working.classList.add("hidden");
    report.classList.remove("hidden");
  } catch (err) {
    working.classList.add("hidden");
    intake.classList.remove("hidden");
    alert(err.message || "Could not analyze this CV.");
  }
}

function renderAll(data) {
  const cv = data.cv;
  $("who").innerHTML = `${escapeHtml(cv.name)} <small>${escapeHtml(cv.headline || "Resume")} · ${cv.word_count} words</small>`;
  renderOverview(data);
  renderAts(data);
  renderJobs(data);
  renderApply(data);
  renderRead(data);
}

function renderOverview(data) {
  const { cv, ats, jobs } = data;
  $("panel-overview").innerHTML = `
    <div class="grid-2">
      <div class="score-card">
        <div class="muted" style="color:#c9c2b5">ATS score</div>
        <div class="score-num">${ats.score}</div>
        <p>${escapeHtml(ats.band)}</p>
      </div>
      <div>
        ${ats.categories.map((c) => `
          <div class="cat">
            <div class="cat-top"><span>${escapeHtml(c.name)}</span><span>${c.score}%</span></div>
            <div class="bar"><span style="width:${c.score}%"></span></div>
          </div>
        `).join("")}
      </div>
    </div>
    <div class="card" style="margin-top:18px">
      <h3>Read from your CV</h3>
      <p class="muted">${escapeHtml(cv.emails[0] || "No email")} · ${escapeHtml(cv.phones[0] || "No phone")} · ${escapeHtml(cv.location || "Location not found")}</p>
      <div class="chips">${cv.skills.slice(0, 16).map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join("") || "<span class='muted'>No skills extracted</span>"}</div>
    </div>
    <div class="card">
      <h3>Quick wins</h3>
      <ul>${ats.suggestions.slice(0, 5).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
    </div>
    <div class="card">
      <h3>Start applying as ${escapeHtml(jobs.query_role)}</h3>
      <p class="muted">${jobs.jobs.length} matched listings · search the same role on hiring sites</p>
      <div class="portals">
        ${(jobs.designations[0]?.portals || []).map((p) => `<a href="${p.url}" target="_blank" rel="noopener">${escapeHtml(p.name)}</a>`).join("")}
      </div>
    </div>
  `;
}

function renderAts(data) {
  const { ats } = data;
  $("panel-ats").innerHTML = `
    <div class="card">
      <h3>ATS checklist</h3>
      <p class="muted">These are the same signals most parsers and recruiters scan for.</p>
      <div class="checklist" style="margin-top:12px">
        ${ats.checks.map((c) => `
          <div class="check">
            <span class="badge ${c.status}">${c.status}</span>
            <div>
              <strong>${escapeHtml(c.label)}</strong>
              <div class="muted">${escapeHtml(c.tip)} · ${c.earned}/${c.max}</div>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
    ${ats.missing_keywords.length ? `
      <div class="card">
        <h3>Keywords to add if they are true for you</h3>
        <div class="chips">${ats.missing_keywords.map((k) => `<span class="chip">${escapeHtml(k)}</span>`).join("")}</div>
      </div>` : ""}
    <div class="card">
      <h3>Improve this CV</h3>
      <p class="muted">Rewrite the summary and bullets in an ATS-friendly style. Only keep lines that are true.</p>
      <button type="button" class="btn primary sm" id="rewrite-btn">Rewrite for ATS</button>
      <div id="rewrite-out"></div>
    </div>
  `;
  $("rewrite-btn").addEventListener("click", runRewrite);
}

function renderJobs(data) {
  const { jobs } = data;
  const packs = jobs.designations.map((d) => `
    <div class="card">
      <h3>${escapeHtml(d.title)}</h3>
      <p class="muted">Open official search results — already filtered for this designation.</p>
      <div class="portals">
        ${d.portals.map((p) => `<a href="${p.url}" target="_blank" rel="noopener">${escapeHtml(p.name)}</a>`).join("")}
      </div>
    </div>
  `).join("");

  const list = jobs.jobs.length
    ? jobs.jobs.map((j, i) => `
      <div class="card job">
        <div class="match">${j.match}%</div>
        <div>
          <h3>${escapeHtml(j.title)}</h3>
          <div class="muted">${escapeHtml(j.company)} · ${escapeHtml(j.location)} · ${escapeHtml(j.source)}</div>
          <p class="muted">${escapeHtml((j.description || "").replace(/\s+/g, " ").slice(0, 220))}…</p>
        </div>
        <div class="job-actions">
          <a class="link-btn" href="${j.url}" target="_blank" rel="noopener">View</a>
          <button type="button" class="btn ghost sm apply-job" data-idx="${i}">Write apply</button>
        </div>
      </div>
    `).join("")
    : `<div class="card"><p>No live API listings matched right now. Use the LinkedIn and Naukri buttons above — those searches are built from your CV.</p></div>`;

  $("panel-jobs").innerHTML = `
    <div class="card jd-box">
      <h3>Match a pasted job description</h3>
      <p class="muted">Copy a LinkedIn or Naukri JD here to see keyword fit against this CV.</p>
      <textarea id="jd-text" placeholder="Paste the full job description…"></textarea>
      <div class="actions" style="margin-top:12px">
        <button type="button" class="btn primary sm" id="jd-btn">Score this JD</button>
      </div>
      <div id="jd-out"></div>
    </div>
    <p class="muted">${escapeHtml(jobs.sources_note)}</p>
    <h3 style="font-family:Fraunces,serif">Apply by designation</h3>
    ${packs}
    <h3 style="font-family:Fraunces,serif">Matched live jobs</h3>
    ${list}
  `;
  $("jd-btn").addEventListener("click", runJdMatch);
  document.querySelectorAll(".apply-job").forEach((btn) => {
    btn.addEventListener("click", () => applyForJob(Number(btn.dataset.idx)));
  });
}

function renderRead(data) {
  const cv = data.cv;
  $("panel-read").innerHTML = `
    <div class="card">
      <h3>Extracted CV text</h3>
      <p class="muted">This is what an ATS is likely to read. If this looks messy, export a simpler PDF from Word.</p>
      <div class="cv-text">${escapeHtml(cv.text)}</div>
    </div>
  `;
}

function renderApply(data) {
  const apply = data.apply;
  const titles = data.jobs.designations.map((d) => d.title);
  $("panel-apply").innerHTML = `
    <p class="muted">Pick the job title you want to apply for. Copy a LinkedIn post, recruiter note, or cover letter.</p>
    <div class="desig" id="desig-row">
      ${titles.map((t, i) => `<button type="button" class="btn ghost sm ${i === 0 ? "on" : ""}" data-title="${escapeAttr(t)}">${escapeHtml(t)}</button>`).join("")}
    </div>
    <div id="kit">${kitHtml(apply)}</div>
  `;
  $("desig-row").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-title]");
    if (!btn) return;
    $("desig-row").querySelectorAll("button").forEach((b) => b.classList.remove("on"));
    btn.classList.add("on");
    await refreshKit(btn.dataset.title);
  });
  bindCopy();
}

function kitHtml(apply) {
  return `
    <div class="card">
      <h3>Profile titles</h3>
      <p><strong>LinkedIn headline</strong><br>${escapeHtml(apply.linkedin_headline)}</p>
      <p><strong>Naukri headline</strong><br>${escapeHtml(apply.naukri_headline)}</p>
      <p><strong>Naukri resume title</strong><br>${escapeHtml(apply.naukri_resume_title)}</p>
    </div>
    ${block("LinkedIn post", apply.linkedin_post, "linkedin_post")}
    ${block("Recruiter / hiring-manager note", apply.recruiter_note, "recruiter_note")}
    ${block("Easy Apply message", apply.easy_apply, "easy_apply")}
    ${block("Cover letter", apply.cover_letter, "cover_letter")}
    <div class="card">
      <h3>Email subjects</h3>
      <ul>${apply.email_subjects.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
    </div>
  `;
}

function block(title, text, key) {
  return `
    <div class="copy-block card">
      <div class="copy-row">
        <h3>${escapeHtml(title)}</h3>
        <button type="button" class="btn ghost sm copy-btn" data-target="${key}">Copy</button>
      </div>
      <textarea id="${key}">${escapeHtml(text)}</textarea>
    </div>
  `;
}

function bindCopy() {
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const el = document.getElementById(btn.dataset.target);
      await navigator.clipboard.writeText(el.value);
      btn.textContent = "Copied";
      setTimeout(() => { btn.textContent = "Copy"; }, 1200);
    });
  });
}

async function refreshKit(designation, extra = {}) {
  const cv = state.data.cv;
  const fd = new FormData();
  fd.append("designation", designation);
  fd.append("location", state.data.jobs.location || "India");
  fd.append("name", cv.name || "");
  fd.append("headline", cv.headline || "");
  fd.append("skills", (cv.skills || []).join(", "));
  fd.append("years", cv.years_experience || "");
  fd.append("email", cv.emails[0] || "");
  fd.append("phone", cv.phones[0] || "");
  fd.append("metrics", (cv.metrics_found || []).join("|"));
  fd.append("github", cv.github || "");
  fd.append("role_family", cv.role_family || "");
  if (extra.company) fd.append("company", extra.company);
  if (extra.job_title) fd.append("job_title", extra.job_title);
  const res = await fetch("/api/apply-kit", { method: "POST", body: fd });
  const apply = await res.json();
  $("kit").innerHTML = kitHtml(apply);
  bindCopy();
}

function cvFormData(extra = {}) {
  const cv = state.data.cv;
  const fd = new FormData();
  fd.append("name", cv.name || "");
  fd.append("headline", cv.headline || "");
  fd.append("skills", (cv.skills || []).join(", "));
  fd.append("cv_text", cv.text || "");
  fd.append("location", state.data.jobs.location || cv.location || "");
  fd.append("years", cv.years_experience || "");
  fd.append("titles", (cv.titles || []).join(", "));
  fd.append("metrics", (cv.metrics_found || []).join("|"));
  fd.append("experience", (cv.sections && cv.sections.experience) || "");
  Object.entries(extra).forEach(([k, v]) => fd.append(k, v));
  return fd;
}

async function runJdMatch() {
  const jd = $("jd-text").value;
  const res = await fetch("/api/match-jd", { method: "POST", body: cvFormData({ jd_text: jd }) });
  const data = await res.json();
  if (!res.ok) {
    alert(data.detail || "Could not score this JD.");
    return;
  }
  state.lastMissing = data.missing || [];
  $("jd-out").innerHTML = `
    <div class="score-card" style="margin-top:16px">
      <div class="muted" style="color:#c9c2b5">JD match</div>
      <div class="score-num">${data.score}</div>
      <p>${escapeHtml(data.band)}</p>
    </div>
    ${data.title_guess ? `<p><strong>Detected role:</strong> ${escapeHtml(data.title_guess)}</p>` : ""}
    <p><strong>Present</strong></p>
    <div class="chips">${(data.present || []).map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join("") || "<span class='muted'>None</span>"}</div>
    <p><strong>Missing</strong></p>
    <div class="chips">${(data.missing || []).map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join("") || "<span class='muted'>None</span>"}</div>
    <ul>${(data.advice || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
  `;
}

async function runRewrite() {
  const fd = cvFormData({
    designation: state.data.jobs.query_role || "",
    missing: (state.lastMissing || state.data.ats.missing_keywords || []).join(", "),
  });
  const res = await fetch("/api/rewrite", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok) {
    alert(data.detail || "Could not rewrite this CV.");
    return;
  }
  $("rewrite-out").innerHTML = `
    <p style="margin-top:16px"><strong>Headline</strong><br>${escapeHtml(data.resume_headline)}</p>
    <p><strong>Summary</strong><br>${escapeHtml(data.improved_summary)}</p>
    <p><strong>Skills line</strong><br>${escapeHtml(data.skills_line)}</p>
    ${(data.add_if_true || []).length ? `<p class="muted">Add only if true: ${data.add_if_true.map(escapeHtml).join(", ")}</p>` : ""}
    ${(data.rewritten_bullets || []).map((b) => `
      <div class="pair">
        <p class="old">${escapeHtml(b.original || "(new)")}</p>
        <p>${escapeHtml(b.improved)}</p>
      </div>
    `).join("")}
    <p class="muted">${escapeHtml(data.note || "")}</p>
  `;
}

async function applyForJob(idx) {
  const job = state.data.jobs.jobs[idx];
  if (!job) return;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("on", b.dataset.tab === "apply"));
  ["overview", "ats", "jobs", "apply", "read"].forEach((name) => {
    $("panel-" + name).classList.toggle("hidden", name !== "apply");
  });
  await refreshKit(job.title || state.data.jobs.query_role, {
    company: job.company,
    job_title: job.title,
  });
}

function downloadReport() {
  const d = state.data;
  if (!d) return;
  const lines = [
    `Tacob CV report — ${d.cv.name}`,
    `Headline: ${d.cv.headline || ""}`,
    `ATS score: ${d.ats.score} (${d.ats.band})`,
    "",
    "Skills: " + (d.cv.skills || []).join(", "),
    "",
    "Suggestions:",
    ...(d.ats.suggestions || []).map((s) => "- " + s),
    "",
    "Apply as: " + d.jobs.query_role,
    "LinkedIn headline: " + d.apply.linkedin_headline,
    "Naukri headline: " + d.apply.naukri_headline,
    "",
    "LinkedIn post:",
    d.apply.linkedin_post,
    "",
    "Cover letter:",
    d.apply.cover_letter,
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (d.cv.name || "tacob") + "-cv-report.txt";
  a.click();
  URL.revokeObjectURL(a.href);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}
