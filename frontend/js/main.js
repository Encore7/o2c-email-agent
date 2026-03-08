import { getDomElements } from "./dom.js";
import { createModalController } from "./modal/controller.js";
import { loadDashboardData } from "./app/data_loader.js";
import { bindDashboardEvents } from "./app/events.js";
import { createDashboardState, updateEmailInState } from "./app/state.js";

export function bootstrapApp() {
  const dom = getDomElements();
  const state = createDashboardState(dom.dateFilterInputEl?.value || "2026-01-20");

  const modal = createModalController(
    dom,
    () => state.currentEmails,
    (updatedEmail) => updateEmailInState(state, updatedEmail)
  );

  function onCategoryToggle(category) {
    state.selectedCategory = state.selectedCategory === category ? null : category;
    void refresh();
  }

  function highlightBySourceEmailId(previousSourceEmailId, nextSourceEmailId) {
    if (previousSourceEmailId) {
      const previousRow = state.rowsBySourceEmailId.get(previousSourceEmailId);
      previousRow?.classList.remove("selected-row");
    }
    if (nextSourceEmailId) {
      const nextRow = state.rowsBySourceEmailId.get(nextSourceEmailId);
      nextRow?.classList.add("selected-row");
    }
  }

  function onEmailClick(email) {
    const previousSourceEmailId = state.activeSourceEmailId;
    state.activeSourceEmailId = email.source_email_id;
    highlightBySourceEmailId(previousSourceEmailId, state.activeSourceEmailId);
    modal.open(email.id);
  }

  async function refresh() {
    await loadDashboardData({
      dom,
      state,
      onCategoryToggle,
      onEmailClick,
    });
  }

  bindDashboardEvents(dom, state, {
    refresh: () => void refresh(),
    clearFilter: () => void refresh(),
    onDateChange: () => void refresh(),
  });

  modal.bindEvents();

  void refresh();
  setInterval(() => void refresh(), 4000);
}
