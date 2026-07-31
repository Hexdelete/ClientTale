function renderStaffList(containerId, staffMembers) {
  const container = document.getElementById(containerId);
  if (!staffMembers.length) {
    container.innerHTML = '<div class="muted">None added yet.</div>';
    return;
  }
  container.innerHTML = staffMembers
    .map(
      (s) => `
      <div class="staff-list-item" data-staff-row="${s.id}" style="flex-direction:column; align-items:stretch;">
        <div class="staff-view" style="display:flex; justify-content:space-between; align-items:center;">
          <span>${escapeHtml(s.full_name)} &mdash; <span class="muted">${escapeHtml(s.username)}</span>${s.email ? ` &mdash; <span class="muted">${escapeHtml(s.email)}</span>` : ""}</span>
          <span class="row-actions">
            <button class="secondary" data-edit-id="${s.id}">Edit</button>
            <button class="danger" data-delete-id="${s.id}">Delete</button>
          </span>
        </div>
        <div class="staff-edit hidden form-grid" style="margin-top:0.5rem;">
          <div class="field"><input type="text" data-field="first_name" value="${escapeHtml(s.first_name)}" placeholder="First name"></div>
          <div class="field"><input type="text" data-field="last_name" value="${escapeHtml(s.last_name)}" placeholder="Last name"></div>
          <div class="field">
            <select data-field="role">
              <option value="lawyer" ${s.role === "lawyer" ? "selected" : ""}>Lawyer</option>
              <option value="paralegal" ${s.role === "paralegal" ? "selected" : ""}>Paralegal</option>
              <option value="admin" ${s.role === "admin" ? "selected" : ""}>Admin</option>
            </select>
          </div>
          <div class="field span-2"><input type="email" data-field="email" value="${escapeHtml(s.email || "")}" placeholder="Email"></div>
          <div class="field"><input type="text" data-field="username" value="${escapeHtml(s.username)}" placeholder="Username"></div>
          <div class="field span-2"><input type="password" data-field="password" placeholder="New password (leave blank to keep current)"></div>
          <div class="field row-actions">
            <button type="button" class="secondary" data-save-id="${s.id}">Save</button>
            <button type="button" class="secondary" data-cancel-id="${s.id}">Cancel</button>
          </div>
        </div>
      </div>`
    )
    .join("");

  container.querySelectorAll("[data-edit-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = container.querySelector(`[data-staff-row="${btn.dataset.editId}"]`);
      row.querySelector(".staff-view").classList.add("hidden");
      row.querySelector(".staff-edit").classList.remove("hidden");
    });
  });

  container.querySelectorAll("[data-cancel-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = container.querySelector(`[data-staff-row="${btn.dataset.cancelId}"]`);
      row.querySelector(".staff-edit").classList.add("hidden");
      row.querySelector(".staff-view").classList.remove("hidden");
    });
  });

  container.querySelectorAll("[data-save-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const row = container.querySelector(`[data-staff-row="${btn.dataset.saveId}"]`);
      const fields = {};
      row.querySelectorAll("[data-field]").forEach((el) => {
        if (el.dataset.field === "password" && !el.value) return;
        fields[el.dataset.field] = el.value.trim() || null;
      });
      const errorEl = document.getElementById("add-error");
      errorEl.classList.add("hidden");
      try {
        await Api.updateStaff(btn.dataset.saveId, fields);
        loadStaff();
      } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.remove("hidden");
      }
    });
  });

  container.querySelectorAll("[data-delete-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this staff member? If they are assigned to any case, they will be deactivated instead of deleted.")) return;
      try {
        await Api.deleteStaff(btn.dataset.deleteId);
        loadStaff();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

async function loadStaff() {
  const [lawyers, paralegals, admins] = await Promise.all([
    Api.listStaff("lawyer"),
    Api.listStaff("paralegal"),
    Api.listStaff("admin"),
  ]);
  renderStaffList("lawyer-list", lawyers);
  renderStaffList("paralegal-list", paralegals);
  renderStaffList("admin-list", admins);
}

document.addEventListener("DOMContentLoaded", async () => {
  await requireAuth();
  loadStaff();

  document.getElementById("staff-email").addEventListener("input", () => {
    const usernameEl = document.getElementById("new-staff-username");
    if (usernameEl.value.trim()) return;
    const email = document.getElementById("staff-email").value.trim();
    usernameEl.value = email.split("@")[0].toLowerCase();
  });

  document.getElementById("add-staff-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("add-error");
    errorEl.classList.add("hidden");
    try {
      await Api.addStaff({
        first_name: document.getElementById("first-name").value.trim(),
        last_name: document.getElementById("last-name").value.trim(),
        role: document.getElementById("role").value,
        email: document.getElementById("staff-email").value.trim() || null,
        username: document.getElementById("new-staff-username").value.trim(),
        password: document.getElementById("new-staff-password").value,
      });
      document.getElementById("add-staff-form").reset();
      loadStaff();
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.remove("hidden");
    }
  });
});
