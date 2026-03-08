import { fetchJson, updateHealth } from "../api.js";
import { CATEGORY_LABELS, getBaseApi } from "../config.js";
import { clearEmailRows, renderCards, upsertEmailRows } from "../dashboard.js";
import { buildFilterKey } from "./state.js";

function buildDashboardUrl(selectedDate) {
  const params = new URLSearchParams();
  if (selectedDate) params.set("date", selectedDate);
  return `${getBaseApi()}/dashboard?${params.toString()}`;
}

function buildEmailsUrl(selectedCategory, selectedDate) {
  const params = new URLSearchParams();
  if (selectedCategory) params.set("category", selectedCategory);
  if (selectedDate) params.set("date", selectedDate);
  params.set("order", "asc");
  return `${getBaseApi()}/emails?${params.toString()}`;
}

export async function loadDashboardData({ dom, state, onCategoryToggle, onEmailClick }) {
  await updateHealth(dom.healthIndicatorEl);

  dom.tableTitleEl.textContent = state.selectedCategory
    ? `${CATEGORY_LABELS[state.selectedCategory]} Emails`
    : "All Emails";

  try {
    const dashboard = await fetchJson(buildDashboardUrl(state.selectedDate));
    const emailList = await fetchJson(buildEmailsUrl(state.selectedCategory, state.selectedDate));
    state.currentEmails = emailList.emails;

    // Remove stale non-data rows (for example previous error row) before upserting data rows.
    const hasNonDataRow = Array.from(dom.emailsBodyEl.querySelectorAll("tr")).some(
      (row) => !row.dataset.sourceEmailId
    );
    if (hasNonDataRow) {
      dom.emailsBodyEl.innerHTML = "";
    }

    const currentFilterKey = buildFilterKey(state);
    if (currentFilterKey !== state.activeFilterKey) {
      clearEmailRows(dom.emailsBodyEl, state.rowsBySourceEmailId);
      state.activeFilterKey = currentFilterKey;
    }

    renderCards(dom.cardsEl, dashboard.cards, state.selectedCategory, onCategoryToggle);
    upsertEmailRows(
      dom.emailsBodyEl,
      state.currentEmails,
      onEmailClick,
      state.rowsBySourceEmailId,
      state.activeSourceEmailId
    );
  } catch (err) {
    dom.cardsEl.innerHTML = "";
    dom.emailsBodyEl.innerHTML = `<tr><td colspan="6">Failed to load data: ${err.message}</td></tr>`;
    state.rowsBySourceEmailId.clear();
  }
}
