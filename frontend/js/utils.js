export function formatDateTime(value) {
  if (!value) return "-";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

export function kvRow(label, value) {
  return `<div class="k">${label}</div><div class="v">${value}</div>`;
}
