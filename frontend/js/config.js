const backendProtocol = window.location.protocol === "https:" ? "https:" : "http:";
const hostname = window.location.hostname || "localhost";
const backendHost =
  hostname === "0.0.0.0" || hostname === "::" ? "localhost" : hostname;

export const BACKEND_URL = `${backendProtocol}//${backendHost}:8000`;
export const TENANT_ID = "tenant_id";

export const CATEGORY_LABELS = {
  payment_claim: "Payment Claim",
  dispute: "Dispute",
  general_ar_request: "General AR Request",
};

export function getBaseApi() {
  return `${BACKEND_URL}/api/v1/tenants/${TENANT_ID}`;
}
