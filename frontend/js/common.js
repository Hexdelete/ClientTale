function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function copyToClipboard(text) {
  return navigator.clipboard.writeText(text);
}
