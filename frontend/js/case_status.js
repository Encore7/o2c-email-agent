export function normalizeCaseStatus(value) {
  const lowered = (value || "").toLowerCase();
  if (lowered === "open") return "under_review";
  if (lowered === "waiting_customer") return "needs_further_review";
  if (lowered === "resolved") return "reviewed";
  if (["new", "under_review", "reviewed", "needs_further_review"].includes(lowered)) {
    return lowered;
  }
  return "under_review";
}
