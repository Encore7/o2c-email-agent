import { CATEGORY_LABELS, getBaseApi } from "./config.js";
import * as api from "./api.js";
import { formatDateTime, kvRow } from "./utils.js";

export function createModalController(
  dom,
  getCurrentEmails,
  updateEmailInState
) {
  let activeSourceEmailId = null;

  function setActiveTab(tab) {
    const isOverview = tab === "overview";
    const isEvidence = tab === "evidence";
    const isReply = tab === "reply";
    dom.tabOverviewEl.classList.toggle("active", isOverview);
    dom.tabEvidenceEl.classList.toggle("active", isEvidence);
    dom.tabReplyEl.classList.toggle("active", isReply);
    dom.panelOverviewEl.classList.toggle("hidden", !isOverview);
    dom.panelEvidenceEl.classList.toggle("hidden", !isEvidence);
    dom.panelReplyEl.classList.toggle("hidden", !isReply);
  }

  function open(emailId, preferredTab = "overview") {
    const email = getCurrentEmails().find((item) => item.id === emailId);
    if (!email) return;
    activeSourceEmailId = email.source_email_id;
    setActiveTab(preferredTab);

    dom.modalSubjectEl.textContent = email.subject;
    dom.modalSummaryEl.innerHTML = [
      `<span class="chip">${CATEGORY_LABELS[email.category]}</span>`,
      `<span class="chip">Priority: ${email.case_priority || "-"}</span>`,
      `<span class="chip">Case: ${email.case_id}</span>`,
      `<span class="chip">${formatDateTime(email.received_at)}</span>`,
      `<span class="chip">${email.from_email}</span>`,
    ].join("");
    dom.modalBodyEl.textContent = email.body || "";

    const confPct = (email.confidence * 100).toFixed(1);
    dom.modalOverviewEl.innerHTML = `
      <div class="overview-grid">
        <div class="overview-card">
          <div class="small-title">Prediction</div>
          <div class="value-line">${CATEGORY_LABELS[email.category]}</div>
        </div>
        <div class="overview-card confidence-wrap">
          <div class="small-title">Confidence</div>
          <div class="value-line">${confPct}%</div>
          <div class="confidence-track">
            <div class="confidence-fill" style="width: ${confPct}%"></div>
          </div>
        </div>
        <div class="overview-card full">
          <div class="small-title">Case Summary</div>
          <div class="value-line">${email.case_summary || "-"}</div>
        </div>
        <div class="overview-card">
          <div class="small-title">Recommended Action</div>
          <div class="value-line">${email.next_best_action || "-"}</div>
        </div>
        <div class="overview-card">
          <div class="small-title">Action Reason</div>
          <div class="value-line">${email.next_best_action_reason || "-"}</div>
        </div>
      </div>
    `;

    dom.modalClassificationEl.innerHTML = `
      <div class="kv">
        ${kvRow("Predicted Category", CATEGORY_LABELS[email.category])}
        ${kvRow("Confidence", `${confPct}%`)}
        ${kvRow("Prediction Source", email.classification_source)}
        ${kvRow("Reason", email.reason)}
      </div>
    `;

    dom.modalExtractionEl.innerHTML = `
      <div class="kv">
        ${kvRow("Extraction Source", email.extraction_source)}
        ${kvRow("Customer", email.customer_name || "-")}
        ${kvRow("Invoices", (email.invoice_references || []).join(", ") || "-")}
        ${kvRow("Amounts", (email.amounts || []).join(", ") || "-")}
        ${kvRow("Dates", (email.mentioned_dates || []).join(", ") || "-")}
        ${kvRow("Detail", email.detail || "-")}
      </div>
    `;

    const invoiceMatches = email.invoice_matches || [];
    const invoiceRows = invoiceMatches
      .map(
        (m) => `
          <tr>
            <td>${m.invoice_id ?? "-"}</td>
            <td>${m.amount ?? "-"}</td>
            <td>${m.status ?? "-"}</td>
            <td>${m.match_confidence !== undefined ? `${(m.match_confidence * 100).toFixed(0)}%` : "-"}</td>
          </tr>
        `
      )
      .join("");

    dom.modalInvoiceEl.innerHTML = `
      <div class="kv">
        ${kvRow("Invoice Match Summary", email.invoice_match_summary || "-")}
      </div>
      ${
        invoiceMatches.length
          ? `
        <div class="match-table-wrap">
          <table class="match-table">
            <thead>
              <tr>
                <th>Invoice ID</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Match Confidence</th>
              </tr>
            </thead>
            <tbody>
              ${invoiceRows}
            </tbody>
          </table>
        </div>
      `
          : `<div class="small-title">No matched invoice rows.</div>`
      }
    `;

    dom.modalReplyEl.innerHTML = `
      <div class="reply-editor">
        <label class="small-title" for="reply-subject-input">Recommended Subject</label>
        <input id="reply-subject-input" class="reply-input" type="text" />
        <label class="small-title" for="reply-body-input">Recommended Reply</label>
        <textarea id="reply-body-input" class="reply-textarea"></textarea>
      </div>
    `;
    const subjectInput = document.getElementById("reply-subject-input");
    const bodyInput = document.getElementById("reply-body-input");
    if (subjectInput) subjectInput.value = email.reply_draft_subject || "";
    if (bodyInput) bodyInput.value = email.reply_draft_body || "";
    if (dom.modalStatusSelectEl) dom.modalStatusSelectEl.value = normalizeCaseStatus(email.case_status);

    dom.modalEl.classList.remove("hidden");
  }

  function close() {
    activeSourceEmailId = null;
    dom.modalEl.classList.add("hidden");
  }

  async function sendReply() {
    if (!activeSourceEmailId) return;
    try {
      const subjectInput = document.getElementById("reply-subject-input");
      const bodyInput = document.getElementById("reply-body-input");
      const reply_subject = subjectInput ? subjectInput.value : "";
      const reply_body = bodyInput ? bodyInput.value : "";
      const response = await api.postJson(`${getBaseApi()}/emails/${activeSourceEmailId}/gmail-draft`, {
        reply_subject,
        reply_body,
      });
      const updated = response.email;
      updateEmailInState(updated);
      open(updated.id, "reply");
      alert(`Gmail draft created (ID: ${response.draft_id}) and logged to DB.`);
    } catch (err) {
      alert(`Failed to create Gmail draft: ${err.message}`);
    }
  }

  async function saveStatus() {
    if (!activeSourceEmailId || !dom.modalStatusSelectEl) return;
    try {
      const patch = api.patchJson
        ? api.patchJson
        : async (url, payload) => {
            const res = await fetch(url, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            if (!res.ok) {
              throw new Error(`${res.status} ${await res.text()}`);
            }
            return res.json();
          };
      const response = await patch(`${getBaseApi()}/emails/${activeSourceEmailId}/status`, {
        status: dom.modalStatusSelectEl.value,
      });
      const updated = response.email;
      updateEmailInState(updated);
      open(updated.id);
      alert("Status updated.");
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    }
  }

  function bindEvents() {
    dom.modalCloseBtnEl.addEventListener("click", close);
    dom.saveStatusBtnEl?.addEventListener("click", saveStatus);
    dom.sendReplyBtnEl.addEventListener("click", sendReply);
    dom.tabOverviewEl.addEventListener("click", () => setActiveTab("overview"));
    dom.tabEvidenceEl.addEventListener("click", () => setActiveTab("evidence"));
    dom.tabReplyEl.addEventListener("click", () => setActiveTab("reply"));
    dom.modalEl.addEventListener("click", (event) => {
      if (event.target === dom.modalEl) close();
    });
  }

  return { open, close, bindEvents };
}

function normalizeCaseStatus(value) {
  const lowered = (value || "").toLowerCase();
  if (lowered === "open") return "under_review";
  if (lowered === "waiting_customer") return "needs_further_review";
  if (lowered === "resolved") return "reviewed";
  if (["new", "under_review", "reviewed", "needs_further_review"].includes(lowered)) return lowered;
  return "under_review";
}
