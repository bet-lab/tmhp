/**
 * ⑨c Anchor copy: shows a small # button next to each h2/h3 on hover;
 * clicking it copies the absolute URL with anchor to the clipboard.
 */
(function () {
  "use strict";
  const article = document.querySelector("article.yue, .yue");
  if (!article) return;

  article.querySelectorAll("h2[id], h3[id]").forEach(h => {
    const btn = document.createElement("button");
    btn.className = "anchor-copy";
    btn.type = "button";
    btn.textContent = "#";
    btn.setAttribute("aria-label", `Copy link to ${h.textContent.trim()}`);
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const url = `${window.location.origin}${window.location.pathname}#${h.id}`;
      try {
        await navigator.clipboard.writeText(url);
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 1200);
      } catch {
        const r = document.createRange();
        const tmp = document.createElement("span");
        tmp.textContent = url; document.body.appendChild(tmp);
        r.selectNode(tmp);
        getSelection().removeAllRanges();
        getSelection().addRange(r);
        document.execCommand("copy");
        tmp.remove();
      }
    });
    h.appendChild(btn);
  });
})();
