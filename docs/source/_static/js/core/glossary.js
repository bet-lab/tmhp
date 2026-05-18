/**
 * ⑥ Inline glossary popovers.
 *
 * Wraps an existing `<span class="glossary" data-term="xxx">` in any
 * page with hover/focus → small popover showing the term name, a 1-2
 * line definition, and a link to the concept page. Terms come from
 * /_static/data/glossary.json.
 */
(function () {
  "use strict";

  const STATE = { terms: null, active: null, pop: null };

  function staticDir() {
    const parts = window.location.pathname.replace(/\/$/, "").split("/").filter(Boolean);
    return parts.length ? "../".repeat(parts.length - 1) + "_static" : "_static";
  }

  async function loadTerms() {
    if (STATE.terms) return STATE.terms;
    const r = await fetch(`${staticDir()}/data/glossary.json`, { credentials: "same-origin" });
    STATE.terms = await r.json();
    return STATE.terms;
  }

  function ensurePopover() {
    if (STATE.pop) return STATE.pop;
    const el = document.createElement("div");
    el.className = "glossary-pop";
    el.setAttribute("role", "tooltip");
    document.body.appendChild(el);
    STATE.pop = el;
    return el;
  }

  function show(span, entry, baseUrl) {
    const pop = ensurePopover();
    pop.innerHTML = `
      <div class="head">${entry.name}</div>
      <div class="def">${entry.def}</div>
      <a class="link" href="${baseUrl}/${entry.link}">↳ Concepts page</a>
    `;
    const r = span.getBoundingClientRect();
    pop.style.top = `${window.scrollY + r.bottom + 4}px`;
    pop.style.left = `${window.scrollX + r.left}px`;
    pop.classList.add("visible");
    STATE.active = span;
  }

  function hide() {
    if (STATE.pop) STATE.pop.classList.remove("visible");
    STATE.active = null;
  }

  async function attach() {
    const spans = document.querySelectorAll("span.glossary[data-term]");
    if (!spans.length) return;
    const terms = await loadTerms();
    const baseUrl = staticDir().replace(/\/_static$/, "");

    spans.forEach(span => {
      const term = terms[span.dataset.term];
      if (!term) return;
      span.tabIndex = 0;
      span.setAttribute("aria-label", term.name);

      span.addEventListener("mouseenter", () => show(span, term, baseUrl));
      span.addEventListener("mouseleave", (e) => {
        const next = e.relatedTarget;
        if (next && STATE.pop && STATE.pop.contains(next)) return;
        hide();
      });
      span.addEventListener("focus", () => show(span, term, baseUrl));
      span.addEventListener("blur", hide);
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
    document.addEventListener("click", (e) => {
      if (STATE.active && !STATE.active.contains(e.target) &&
          STATE.pop && !STATE.pop.contains(e.target)) hide();
    });
  }

  window.tmhpGlossary = { attach };
})();
