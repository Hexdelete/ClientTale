const STRING_IDS = [
  "case_number", "case_type", "county", "judge",
  "injured_first_name", "injured_last_name", "ssn", "height", "weight",
  "client_first_name", "client_last_name", "address_line1", "address_line2",
  "city", "state", "zip", "country", "work_phone", "email",
  "case_synopsis", "intake_comments",
];
const DATE_IDS = ["date_of_event", "sol_date", "conf_int_check_date", "dob", "dod"];
const INT_IDS = ["age"];
const FK_IDS = ["primary_lawyer_id", "secondary_lawyer_id", "legal_assistant_id"];

let currentCaseId = null;
let lawyerOptions = [];
let paralegalOptions = [];
let currentOpposingCounsel = [];

function qs(id) { return document.getElementById(id); }

function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      qs(btn.dataset.tab).classList.add("active");
    });
  });
}

function populateSelect(select, options, selectedId) {
  select.innerHTML = '<option value="">-- unassigned --</option>' +
    options.map((o) => `<option value="${o.id}">${escapeHtml(o.full_name)}</option>`).join("");
  if (selectedId) select.value = selectedId;
}

function sortByFullName(options) {
  return [...options].sort((a, b) => a.full_name.localeCompare(b.full_name));
}

async function loadStaffDropdowns(selected = {}) {
  const [lawyers, paralegals] = await Promise.all([Api.listStaff("lawyer"), Api.listStaff("paralegal")]);
  lawyerOptions = sortByFullName(lawyers);
  paralegalOptions = sortByFullName(paralegals);
  populateSelect(qs("primary_lawyer_id"), lawyerOptions, selected.primary_lawyer_id);
  populateSelect(qs("secondary_lawyer_id"), lawyerOptions, selected.secondary_lawyer_id);
  populateSelect(qs("legal_assistant_id"), paralegalOptions, selected.legal_assistant_id);
}

function fillForm(data) {
  STRING_IDS.forEach((id) => { if (qs(id)) qs(id).value = data[id] || ""; });
  DATE_IDS.forEach((id) => { if (qs(id)) qs(id).value = data[id] || ""; });
  INT_IDS.forEach((id) => { if (qs(id)) qs(id).value = data[id] != null ? data[id] : ""; });
  if (data.status) qs("status").value = data.status;
}

function collectForm() {
  const payload = {};
  STRING_IDS.forEach((id) => { payload[id] = qs(id).value.trim() || null; });
  DATE_IDS.forEach((id) => { payload[id] = qs(id).value || null; });
  INT_IDS.forEach((id) => { payload[id] = qs(id).value || null; });
  FK_IDS.forEach((id) => { payload[id] = qs(id).value || null; });
  payload.status = qs("status").value;
  payload.case_number = qs("case_number").value.trim();
  return payload;
}

function updateTitle(data) {
  const name = `${data.injured_first_name || ""} ${data.injured_last_name || ""}`.trim();
  qs("page-title").textContent = name || `Case #${data.case_number}`;
}

async function loadEvents() {
  const caseData = await Api.getCase(currentCaseId);
  const body = qs("events-body");
  if (!caseData.events.length) {
    body.innerHTML = '<tr><td colspan="4" class="muted">No events yet.</td></tr>';
    return;
  }
  body.innerHTML = caseData.events
    .map(
      (e) => `
      <tr>
        <td>${escapeHtml(e.event_date)}${e.event_time ? ` ${escapeHtml(e.event_time)}` : ""}</td>
        <td>${escapeHtml(e.event_type)}</td>
        <td>${escapeHtml(e.description || "")}</td>
        <td><button class="danger" data-del-event="${e.id}">Delete</button></td>
      </tr>`
    )
    .join("");

  body.querySelectorAll("[data-del-event]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this event?")) return;
      await Api.deleteEvent(currentCaseId, btn.dataset.delEvent);
      loadEvents();
    });
  });
}

async function loadOpposingCounsel() {
  const caseData = await Api.getCase(currentCaseId);
  currentOpposingCounsel = caseData.opposing_counsel;
  const body = qs("opposing-counsel-body");
  if (!currentOpposingCounsel.length) {
    body.innerHTML = '<tr><td colspan="5" class="muted">No opposing counsel added yet.</td></tr>';
    return;
  }
  body.innerHTML = currentOpposingCounsel
    .map(
      (oc) => `
      <tr>
        <td>${escapeHtml(oc.name || "")}</td>
        <td>${escapeHtml(oc.firm || "")}</td>
        <td>${escapeHtml(oc.phone || "")}</td>
        <td>${escapeHtml(oc.email || "")}</td>
        <td><button class="danger" data-del-oc="${oc.id}">Delete</button></td>
      </tr>`
    )
    .join("");

  body.querySelectorAll("[data-del-oc]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this opposing counsel entry?")) return;
      await Api.deleteOpposingCounsel(currentCaseId, btn.dataset.delOc);
      loadOpposingCounsel();
    });
  });
}

function bestStaffMatch(name, options) {
  if (!name) return "";
  const normalized = name.trim().toLowerCase();
  const match = options.find((o) => o.full_name.toLowerCase() === normalized);
  return match ? match.id : "";
}

let pendingImport = null;

function renderImportReview(parsed) {
  pendingImport = parsed;
  qs("import-review").classList.remove("hidden");
  const staffFieldsEl = qs("import-staff-fields");
  const primaryMatch = bestStaffMatch(parsed.primary_lawyer_name, lawyerOptions);
  const secondaryMatch = bestStaffMatch(parsed.secondary_lawyer_name, lawyerOptions);
  const assistantMatch = bestStaffMatch(parsed.legal_assistant_name, paralegalOptions);

  staffFieldsEl.innerHTML = `
    <div class="form-grid">
      <div class="field">
        <label>Primary Lawyer (parsed: "${escapeHtml(parsed.primary_lawyer_name || "")}")</label>
        <select id="import-primary"></select>
      </div>
      <div class="field">
        <label>Secondary Lawyer (parsed: "${escapeHtml(parsed.secondary_lawyer_name || "")}")</label>
        <select id="import-secondary"></select>
      </div>
      <div class="field">
        <label>Paralegal (parsed: "${escapeHtml(parsed.legal_assistant_name || "")}")</label>
        <select id="import-assistant"></select>
      </div>
    </div>`;
  populateSelect(qs("import-primary"), lawyerOptions, primaryMatch);
  populateSelect(qs("import-secondary"), lawyerOptions, secondaryMatch);
  populateSelect(qs("import-assistant"), paralegalOptions, assistantMatch);
}

async function handlePdfImport(file) {
  const statusEl = qs("pdf-status");
  statusEl.textContent = "Parsing PDF...";
  try {
    const parsed = await Api.importPdf(file);
    statusEl.textContent = "Parsed. Review below before applying.";
    renderImportReview(parsed);
  } catch (err) {
    statusEl.textContent = `Import failed: ${err.message}`;
  }
}

function applyImport() {
  if (!pendingImport) return;
  fillForm(pendingImport);
  qs("primary_lawyer_id").value = qs("import-primary").value;
  qs("secondary_lawyer_id").value = qs("import-secondary").value;
  qs("legal_assistant_id").value = qs("import-assistant").value;
  qs("import-review").classList.add("hidden");
  qs("pdf-status").textContent = "Imported data applied to form. Review and save.";
  pendingImport = null;
}

function showSavedSections() {
  qs("opposing-counsel-placeholder").classList.add("hidden");
  qs("opposing-counsel-content").classList.remove("hidden");
  qs("events-placeholder").classList.add("hidden");
  qs("events-content").classList.remove("hidden");
}

async function loadExistingCase(id) {
  currentCaseId = id;
  const data = await Api.getCase(id);
  updateTitle(data);
  fillForm(data);
  await loadStaffDropdowns(data);
  qs("delete-case-btn").classList.remove("hidden");
  qs("pdf-import-block").classList.add("hidden");
  showSavedSections();
  await Promise.all([loadEvents(), loadOpposingCounsel()]);
}

document.addEventListener("DOMContentLoaded", async () => {
  await requireAuth();
  initTabs();

  const params = new URLSearchParams(location.search);
  const id = params.get("id");

  if (id) {
    await loadExistingCase(id);
  } else {
    await loadStaffDropdowns();
    qs("opposing-counsel-placeholder").classList.remove("hidden");
    qs("events-placeholder").classList.remove("hidden");
  }

  qs("pdf-file").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handlePdfImport(file);
  });

  qs("apply-import").addEventListener("click", applyImport);
  qs("dismiss-import").addEventListener("click", () => {
    pendingImport = null;
    qs("import-review").classList.add("hidden");
  });

  qs("case-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = qs("form-error");
    errorEl.classList.add("hidden");
    const payload = collectForm();
    try {
      if (currentCaseId) {
        const updated = await Api.updateCase(currentCaseId, payload);
        updateTitle(updated);
      } else {
        const created = await Api.createCase(payload);
        location.href = `case.html?id=${created.id}`;
        return;
      }
      qs("pdf-status").textContent = "Saved.";
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.remove("hidden");
    }
  });

  qs("delete-case-btn").addEventListener("click", async () => {
    if (!confirm("Delete this case and all of its events? This cannot be undone.")) return;
    await Api.deleteCase(currentCaseId);
    location.href = "index.html";
  });

  qs("copy-emails-btn").addEventListener("click", async () => {
    const statusEl = qs("copy-emails-status");
    const staffEmail = (id, options) => {
      const match = options.find((o) => String(o.id) === qs(id).value);
      return match ? match.email : null;
    };
    const emails = [
      ...currentOpposingCounsel.map((oc) => oc.email),
      staffEmail("primary_lawyer_id", lawyerOptions),
      staffEmail("secondary_lawyer_id", lawyerOptions),
      staffEmail("legal_assistant_id", paralegalOptions),
    ]
      .map((e) => (e || "").trim())
      .filter(Boolean);
    const unique = [...new Set(emails)];

    if (!unique.length) {
      statusEl.textContent = "No emails to copy.";
      return;
    }
    try {
      await copyToClipboard(unique.join(", "));
      statusEl.textContent = `Copied ${unique.length} email${unique.length === 1 ? "" : "s"}.`;
    } catch (err) {
      statusEl.textContent = "Copy failed.";
    }
  });

  qs("add-event-btn").addEventListener("click", async () => {
    if (!currentCaseId) {
      alert("Save the case before adding events.");
      return;
    }
    const eventDate = qs("event_date").value;
    if (!eventDate) {
      alert("Event date is required.");
      return;
    }
    await Api.addEvent(currentCaseId, {
      event_date: eventDate,
      event_time: qs("event_time").value || null,
      event_type: qs("event_type").value,
      description: qs("event_description").value.trim() || null,
    });
    qs("event_date").value = "";
    qs("event_time").value = "";
    qs("event_description").value = "";
    loadEvents();
  });

  qs("export-ics-btn").addEventListener("click", () => {
    if (!currentCaseId) {
      alert("Save the case before exporting events.");
      return;
    }
    location.href = `/api/cases/${currentCaseId}/events/export.ics`;
  });

  qs("add-opposing-counsel-btn").addEventListener("click", async () => {
    if (!currentCaseId) {
      alert("Save the case before adding opposing counsel.");
      return;
    }
    await Api.addOpposingCounsel(currentCaseId, {
      name: qs("oc_name").value.trim() || null,
      firm: qs("oc_firm").value.trim() || null,
      phone: qs("oc_phone").value.trim() || null,
      email: qs("oc_email").value.trim() || null,
    });
    qs("oc_name").value = "";
    qs("oc_firm").value = "";
    qs("oc_phone").value = "";
    qs("oc_email").value = "";
    loadOpposingCounsel();
  });
});
