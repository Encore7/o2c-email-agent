import { CATEGORY_LABELS } from "../config.js";
import { formatDateTime, kvRow } from "../utils.js";

export function renderModalHeader(dom, email) {
  dom.modalSubjectEl.textContent = email.subject;
  dom.modalSummaryEl.innerHTML = [
    `<span class="chip">${CATEGORY_LABELS[email.category]}</span>`,
    `<span class="chip">Priority: ${email.case_priority || "-"}</span>`,
    `<span class="chip">Case: ${email.case_id}</span>`,
    `<span class="chip">${formatDateTime(email.received_at)}</span>`,
    `<span class="chip">${email.from_email}</span>`,
  ].join("");
  dom.modalBodyEl.textContent = email.body || "";
}

export function renderOverview(dom, email) {
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
}

export function renderClassification(dom, email) {
  const confPct = (email.confidence * 100).toFixed(1);
  dom.modalClassificationEl.innerHTML = `
    <div class="kv">
      ${kvRow("Predicted Category", CATEGORY_LABELS[email.category])}
      ${kvRow("Confidence", `${confPct}%`)}
      ${kvRow("Prediction Source", email.classification_source)}
      ${kvRow("Reason", email.reason)}
    </div>
  `;
}

export function renderExtraction(dom, email) {
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
}

export function renderInvoiceEvidence(dom, email) {
  const invoiceMatches = email.invoice_matches || [];
  const invoiceRows = invoiceMatches
    .map(
      (match) => `
      <tr>
        <td>${match.invoice_id ?? "-"}</td>
        <td>${match.amount ?? "-"}</td>
        <td>${match.status ?? "-"}</td>
        <td>${
          match.match_confidence !== undefined
            ? `${(match.match_confidence * 100).toFixed(0)}%`
            : "-"
        }</td>
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
        : '<div class="small-title">No matched invoice rows.</div>'
    }
  `;
}

export function renderAllEvidence(dom, email) {
  renderOverview(dom, email);
  renderClassification(dom, email);
  renderExtraction(dom, email);
  renderInvoiceEvidence(dom, email);
}
