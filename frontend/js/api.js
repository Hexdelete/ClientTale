const Api = (() => {
  async function request(path, options = {}) {
    const res = await fetch(`/api${path}`, {
      credentials: "same-origin",
      headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
      ...options,
    });

    if (res.status === 401) {
      if (!location.pathname.endsWith("login.html")) {
        location.href = "login.html";
      }
      throw new Error("authentication required");
    }

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await res.json() : null;

    if (!res.ok) {
      throw new Error((data && data.error) || `request failed (${res.status})`);
    }
    return data;
  }

  return {
    get: (path) => request(path),
    post: (path, body) => request(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body) }),
    put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body) }),
    del: (path) => request(path, { method: "DELETE" }),

    me: () => request("/auth/me"),
    login: (username, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
    logout: () => request("/auth/logout", { method: "POST" }),

    listStaff: (role) => request(`/staff${role ? `?role=${encodeURIComponent(role)}` : ""}`),
    addStaff: (payload) => request("/staff", { method: "POST", body: JSON.stringify(payload) }),
    updateStaff: (id, payload) => request(`/staff/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
    deleteStaff: (id) => request(`/staff/${id}`, { method: "DELETE" }),

    listCases: (search) => request(`/cases${search ? `?search=${encodeURIComponent(search)}` : ""}`),
    getCase: (id) => request(`/cases/${id}`),
    createCase: (payload) => request("/cases", { method: "POST", body: JSON.stringify(payload) }),
    updateCase: (id, payload) => request(`/cases/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
    deleteCase: (id) => request(`/cases/${id}`, { method: "DELETE" }),

    addEvent: (caseId, payload) => request(`/cases/${caseId}/events`, { method: "POST", body: JSON.stringify(payload) }),
    updateEvent: (caseId, eventId, payload) => request(`/cases/${caseId}/events/${eventId}`, { method: "PUT", body: JSON.stringify(payload) }),
    deleteEvent: (caseId, eventId) => request(`/cases/${caseId}/events/${eventId}`, { method: "DELETE" }),

    addOpposingCounsel: (caseId, payload) => request(`/cases/${caseId}/opposing-counsel`, { method: "POST", body: JSON.stringify(payload) }),
    updateOpposingCounsel: (caseId, counselId, payload) => request(`/cases/${caseId}/opposing-counsel/${counselId}`, { method: "PUT", body: JSON.stringify(payload) }),
    deleteOpposingCounsel: (caseId, counselId) => request(`/cases/${caseId}/opposing-counsel/${counselId}`, { method: "DELETE" }),

    upcomingEvents: (days) => request(`/events/upcoming${days ? `?days=${days}` : ""}`),

    importPdf: (file) => {
      const form = new FormData();
      form.append("file", file);
      return request("/import/pdf", { method: "POST", body: form });
    },
  };
})();
