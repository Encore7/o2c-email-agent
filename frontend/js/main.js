import { CATEGORY_LABELS, getBaseApi } from "./config.js";
import { fetchJson, updateHealth } from "./api.js";
import { getDomElements } from "./dom.js";
import { clearEmailRows, renderCards, upsertEmailRows } from "./dashboard.js";
import { createModalController } from "./modal.js";

export function bootstrapApp() {
  const dom = getDomElements();
  let selectedCategory = null;
  let currentEmails = [];
  let selectedDate = dom.dateFilterInputEl?.value || "2026-01-20";
  let activeSourceEmailId = null;
  let activeFilterKey = "";
  const rowsBySourceEmailId = new Map();

  const modal = createModalController(
    dom,
    () => currentEmails,
    (updatedEmail) => {
      const idx = currentEmails.findIndex((e) => e.source_email_id === updatedEmail.source_email_id);
      if (idx >= 0) currentEmails[idx] = updatedEmail;
    }
  );

  function onCategoryToggle(category) {
    selectedCategory = selectedCategory === category ? null : category;
    loadData();
  }

  function openEmail(email) {
    activeSourceEmailId = email.source_email_id;
    modal.open(email.id);
  }

  async function loadData() {
    await updateHealth(dom.healthIndicatorEl);
    dom.tableTitleEl.textContent = selectedCategory
      ? `${CATEGORY_LABELS[selectedCategory]} Emails`
      : "All Emails";
    try {
      const dashboardParams = new URLSearchParams();
      if (selectedDate) dashboardParams.set("date", selectedDate);
      const dashboard = await fetchJson(`${getBaseApi()}/dashboard?${dashboardParams.toString()}`);

      const emailParams = new URLSearchParams();
      if (selectedCategory) emailParams.set("category", selectedCategory);
      if (selectedDate) emailParams.set("date", selectedDate);
      emailParams.set("order", "asc");
      const emailList = await fetchJson(`${getBaseApi()}/emails?${emailParams.toString()}`);
      currentEmails = emailList.emails;

      const currentFilterKey = `${selectedCategory || "all"}|${selectedDate || "all"}`;
      if (currentFilterKey !== activeFilterKey) {
        clearEmailRows(dom.emailsBodyEl, rowsBySourceEmailId);
        activeFilterKey = currentFilterKey;
      }

      renderCards(dom.cardsEl, dashboard.cards, selectedCategory, onCategoryToggle);
      upsertEmailRows(
        dom.emailsBodyEl,
        currentEmails,
        openEmail,
        rowsBySourceEmailId,
        activeSourceEmailId
      );
    } catch (err) {
      dom.cardsEl.innerHTML = "";
      dom.emailsBodyEl.innerHTML = `<tr><td colspan="5">Failed to load data: ${err.message}</td></tr>`;
      rowsBySourceEmailId.clear();
    }
  }

  dom.refreshBtnEl.addEventListener("click", loadData);
  dom.dateFilterInputEl?.addEventListener("change", () => {
    selectedDate = dom.dateFilterInputEl.value;
    loadData();
  });
  dom.clearFilterBtnEl.addEventListener("click", () => {
    selectedCategory = null;
    loadData();
  });
  modal.bindEvents();

  loadData();
  setInterval(loadData, 4000);
}
