export function createDashboardState(initialDate = "2026-01-20") {
  return {
    selectedCategory: null,
    currentEmails: [],
    selectedDate: initialDate,
    activeSourceEmailId: null,
    activeFilterKey: "",
    rowsBySourceEmailId: new Map(),
  };
}

export function updateEmailInState(state, updatedEmail) {
  const idx = state.currentEmails.findIndex((email) => email.source_email_id === updatedEmail.source_email_id);
  if (idx >= 0) {
    state.currentEmails[idx] = updatedEmail;
  }
}

export function buildFilterKey(state) {
  return `${state.selectedCategory || "all"}|${state.selectedDate || "all"}`;
}
