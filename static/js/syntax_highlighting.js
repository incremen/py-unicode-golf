function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function syntaxHighlight(text) {
  // Extract strings before escaping so we can find real quotes
  const strings = [];
  let safe = text.replace(/b'[^']*'|b"[^"]*"|'[^']*'|"[^"]*"/g, m => {
    strings.push(m);
    return `__STR${strings.length - 1}__`;
  });

  let escaped = escapeHtml(safe)
    .replace(/\b([a-z_]+)(?=\()/g, '<span class="syn-fn">$1</span>')
    .replace(/\b(\d+)\b/g, '<span class="syn-num">$1</span>')
    .replace(/\b(True|False|None)\b/g, '<span class="syn-bool">$1</span>')
    .replace(/([()])/g, '<span class="syn-paren">$1</span>');

  for (let i = 0; i < strings.length; i++) {
    escaped = escaped.replace(`__STR${i}__`, `<span class="syn-str">${escapeHtml(strings[i])}</span>`);
  }
  return escaped;
}
