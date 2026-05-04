
export function storyBodyHtml(body) {
  if (!body) return "";

  const escaped = htmlEscape(String(body));   // single escape pass
  const paragraphs = escaped.split(/\n\s*\n/);

  return paragraphs.map(para => {
    const lines = para.split("\n");
    const bulletPattern = /^[\s]*[-*]\s+/;
    const isList = lines.length > 1 &&
                   lines.every(l => l.trim() === "" || bulletPattern.test(l));

    if (isList) {
      const items = lines
        .filter(l => bulletPattern.test(l))
        .map(l => l.replace(bulletPattern, ""))
        .map(t => boldOnly(t))                 // text already escaped above
        .map(t => `<li>${t}</li>`)
        .join("");
      return `<ul>${items}</ul>`;
    }

    return `<p>${boldOnly(para).replace(/\n/g, "<br/>")}</p>`;
  }).join("");
}

export function inlineMd(text) {
  if (!text) return "";
  return boldOnly(htmlEscape(String(text)));
}

function boldOnly(text) {
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function htmlEscape(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
