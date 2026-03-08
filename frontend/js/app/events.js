export function bindDashboardEvents(dom, state, handlers) {
  const { refresh, clearFilter, onDateChange } = handlers;

  dom.refreshBtnEl.addEventListener("click", refresh);

  dom.dateFilterInputEl?.addEventListener("change", () => {
    state.selectedDate = dom.dateFilterInputEl.value;
    onDateChange();
  });

  dom.clearFilterBtnEl.addEventListener("click", () => {
    state.selectedCategory = null;
    clearFilter();
  });
}
