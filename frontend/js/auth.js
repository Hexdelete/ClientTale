async function requireAuth() {
  try {
    const user = await Api.me();
    const el = document.getElementById("current-user");
    if (el) el.textContent = user.username;
    return user;
  } catch (e) {
    location.href = "login.html";
    return null;
  }
}

function wireLogout() {
  const btn = document.getElementById("logout-btn");
  if (btn) {
    btn.addEventListener("click", async () => {
      await Api.logout();
      location.href = "login.html";
    });
  }
}

document.addEventListener("DOMContentLoaded", wireLogout);
