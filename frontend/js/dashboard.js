function statusPillClass(status) {
  const key = (status || "").toLowerCase();
  if (key.includes("pending")) return "status-pending";
  if (key.includes("open")) return "status-open";
  if (key.includes("settl")) return "status-settled";
  if (key.includes("closed")) return "status-closed";
  if (key.includes("declin")) return "status-declined";
  return "";
}

function renderUpcomingRows(events) {
  const body = document.getElementById("upcoming-body");
  if (!events.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted">No upcoming events.</td></tr>';
    return;
  }
  body.innerHTML = events
    .map(
      (e) => `
      <tr>
        <td>${escapeHtml(e.event_date)}</td>
        <td>${escapeHtml(e.event_type)}</td>
        <td><a href="case.html?id=${e.case_id}">${escapeHtml(e.case_number)}</a></td>
        <td>${escapeHtml(e.client_name)}</td>
        <td><span class="pill ${statusPillClass(e.status)}">${escapeHtml(e.status)}</span></td>
        <td>${escapeHtml(e.description || "")}</td>
      </tr>`
    )
    .join("");
}

function renderUpcomingInline(upcoming) {
  if (!upcoming || !upcoming.length) {
    return '<div class="upcoming-inline"><div class="none">No upcoming events</div></div>';
  }
  const items = upcoming
    .map((e) => `<div class="event-item">${escapeHtml(e.event_date)} — ${escapeHtml(e.event_type)}${e.description ? `: ${escapeHtml(e.description)}` : ""}</div>`)
    .join("");
  return `<div class="upcoming-inline">${items}</div>`;
}

function renderSearchResults(cases) {
  const container = document.getElementById("search-results");
  if (!cases.length) {
    container.innerHTML = '<div class="muted">No matching cases.</div>';
    return;
  }
  container.innerHTML = cases
    .map((c) => {
      const clientName = `${c.client_first_name || ""} ${c.client_last_name || ""}`.trim() || "(no client name)";
      return `
      <div class="case-search-item">
        <div class="case-row">
          <div>
            <div class="case-title"><a href="case.html?id=${c.id}">${escapeHtml(clientName)} — Case #${escapeHtml(c.case_number)}</a></div>
            <div class="case-sub">${escapeHtml(c.case_type || "")} · ${escapeHtml(c.county || "")} · Primary: ${escapeHtml(c.primary_lawyer_name || "unassigned")}</div>
          </div>
          <span class="pill ${statusPillClass(c.status)}">${escapeHtml(c.status)}</span>
        </div>
        ${renderUpcomingInline(c.upcoming_events)}
      </div>`;
    })
    .join("");
}

async function loadUpcoming() {
  try {
    const events = await Api.upcomingEvents();
    renderUpcomingRows(events);
  } catch (e) {
    document.getElementById("upcoming-body").innerHTML = `<tr><td colspan="6" class="error-msg">${escapeHtml(e.message)}</td></tr>`;
  }
}

async function runSearch(term) {
  try {
    const cases = await Api.listCases(term);
    renderSearchResults(cases);
  } catch (e) {
    document.getElementById("search-results").innerHTML = `<div class="error-msg">${escapeHtml(e.message)}</div>`;
  }
}

let searchDebounce;
document.addEventListener("DOMContentLoaded", async () => {
  await requireAuth();
  loadUpcoming();
  runSearch("");

  const input = document.getElementById("search-input");
  input.addEventListener("input", () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => runSearch(input.value.trim()), 250);
  });

  document.getElementById("clear-search").addEventListener("click", () => {
    input.value = "";
    runSearch("");
  });
});
