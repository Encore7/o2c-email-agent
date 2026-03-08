import { getBaseApi } from "../config.js";
import { patchJson, postJson } from "../api.js";
import { normalizeCaseStatus } from "../case_status.js";
import { renderAllEvidence, renderModalHeader } from "./renderers.js";
import { getReplyValues, renderReplyForm, setReplyValues } from "./reply_form.js";
import { setActiveTab } from "./tabs.js";

export function createModalController(dom, getCurrentEmails, updateEmailInState) {
  let activeSourceEmailId = null;

  function findEmailById(emailId) {
    return getCurrentEmails().find((item) => item.id === emailId);
  }

  function open(emailId, preferredTab = "overview") {
    const email = findEmailById(emailId);
    if (!email) return;

    activeSourceEmailId = email.source_email_id;
    setActiveTab(dom, preferredTab);

    renderModalHeader(dom, email);
    renderAllEvidence(dom, email);
    renderReplyForm(dom.modalReplyEl);
    setReplyValues(email);

    if (dom.modalStatusSelectEl) {
      dom.modalStatusSelectEl.value = normalizeCaseStatus(email.case_status);
    }

    dom.modalEl.classList.remove("hidden");
  }

  function close() {
    activeSourceEmailId = null;
    dom.modalEl.classList.add("hidden");
  }

  async function sendReply() {
    if (!activeSourceEmailId) return;

    try {
      const response = await postJson(`${getBaseApi()}/emails/${activeSourceEmailId}/gmail-draft`, getReplyValues());
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
      const response = await patchJson(`${getBaseApi()}/emails/${activeSourceEmailId}/status`, {
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
    dom.tabOverviewEl.addEventListener("click", () => setActiveTab(dom, "overview"));
    dom.tabEvidenceEl.addEventListener("click", () => setActiveTab(dom, "evidence"));
    dom.tabReplyEl.addEventListener("click", () => setActiveTab(dom, "reply"));
    dom.modalEl.addEventListener("click", (event) => {
      if (event.target === dom.modalEl) close();
    });
  }

  return { open, close, bindEvents };
}
