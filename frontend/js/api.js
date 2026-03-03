import { BACKEND_URL } from "./config.js";

export async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function postJson(url, payload = null) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : null,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function patchJson(url, payload = null) {
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : null,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json();
}

export async function updateHealth(healthIndicatorEl) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/health`);
    const healthy = res.ok;
    healthIndicatorEl.classList.toggle("health-up", healthy);
    healthIndicatorEl.classList.toggle("health-down", !healthy);
    healthIndicatorEl.title = healthy ? "Backend healthy" : "Backend unhealthy";
  } catch (_) {
    healthIndicatorEl.classList.remove("health-up");
    healthIndicatorEl.classList.add("health-down");
    healthIndicatorEl.title = "Backend unhealthy";
  }
}
