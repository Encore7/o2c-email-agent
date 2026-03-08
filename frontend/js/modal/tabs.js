export function setActiveTab(dom, tab) {
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
