import { CATEGORY_LABELS } from "./config.js";
import { formatDateTime } from "./utils.js";

export function renderCards(cardsEl, cards, selectedCategory, onCategoryToggle) {
  cardsEl.innerHTML = "";
  cards.forEach((card) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `card ${selectedCategory === card.category ? "active" : ""}`;
    btn.innerHTML = `
      <div class="title">${CATEGORY_LABELS[card.category]}</div>
      <div class="count">${card.count}</div>
    `;
    btn.onclick = () => onCategoryToggle(card.category);
    cardsEl.appendChild(btn);
  });
}

export function clearEmailRows(emailsBodyEl, rowsBySourceEmailId) {
  emailsBodyEl.innerHTML = "";
  rowsBySourceEmailId.clear();
}

export function upsertEmailRows(
  emailsBodyEl,
  emails,
  onEmailClick,
  rowsBySourceEmailId,
  activeSourceEmailId
) {
  const seen = new Set();
  for (const email of emails) {
    seen.add(email.source_email_id);
    const existing = rowsBySourceEmailId.get(email.source_email_id);
    if (existing) {
      updateEmailRow(existing, email, activeSourceEmailId);
    } else {
      const row = buildEmailRow(email, onEmailClick, activeSourceEmailId);
      rowsBySourceEmailId.set(email.source_email_id, row);
      emailsBodyEl.appendChild(row);
    }
  }
  for (const [sourceEmailId, row] of rowsBySourceEmailId.entries()) {
    if (!seen.has(sourceEmailId)) {
      row.remove();
      rowsBySourceEmailId.delete(sourceEmailId);
    }
  }
}

function buildEmailRow(email, onEmailClick, activeSourceEmailId) {
  const tr = document.createElement("tr");
  tr.dataset.sourceEmailId = email.source_email_id;
  tr.addEventListener("click", () => onEmailClick(email));
  updateEmailRow(tr, email, activeSourceEmailId);
  return tr;
}

function updateEmailRow(tr, email, activeSourceEmailId) {
  const priority = (email.case_priority || "medium").toLowerCase();
  const status = normalizeCaseStatus(email.case_status);
  tr.classList.toggle(
    "selected-row",
    Boolean(activeSourceEmailId && activeSourceEmailId === email.source_email_id)
  );
  tr.innerHTML = `
    <td>${formatDateTime(email.received_at)}</td>
    <td>${email.subject}</td>
    <td><span class="pill">${CATEGORY_LABELS[email.category]}</span></td>
    <td>${(email.confidence * 100).toFixed(1)}%</td>
    <td><span class="pill priority-pill priority-${priority}">${priority}</span></td>
    <td><span class="pill status-pill status-${status}">${status.replaceAll("_", " ")}</span></td>
  `;
}

function normalizeCaseStatus(value) {
  const lowered = (value || "").toLowerCase();
  if (lowered === "open") return "under_review";
  if (lowered === "waiting_customer") return "needs_further_review";
  if (lowered === "resolved") return "reviewed";
  if (["new", "under_review", "reviewed", "needs_further_review"].includes(lowered)) return lowered;
  return "under_review";
}
