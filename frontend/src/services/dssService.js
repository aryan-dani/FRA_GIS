const API_URL = (
  process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === "development" ? "http://localhost:5001" : "")
).replace(/\/$/, "");

async function apiFetch(path, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000);

  try {
    const response = await fetch(`${API_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      ...options,
      signal: controller.signal,
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return payload;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(
        "The API is taking too long to respond (Render free tier may be waking up). Retry in a moment."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

function requireApi() {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
}

export async function fetchDssPriority(state) {
  requireApi();
  const q = state ? `?state=${encodeURIComponent(state)}` : "";
  return apiFetch(`/api/dss/priority${q}`);
}

export async function fetchSyntheticClaims({ state, status, limit = 200 } = {}) {
  requireApi();
  const params = new URLSearchParams();
  if (state) params.set("state", state);
  if (status) params.set("status", status);
  if (limit) params.set("limit", String(limit));
  const q = params.toString() ? `?${params}` : "";
  return apiFetch(`/api/dss/synthetic-claims${q}`);
}

export async function fetchSchemeCatalog() {
  requireApi();
  return apiFetch("/api/dss/schemes");
}

export async function predictDss(payload) {
  requireApi();
  return apiFetch("/api/dss/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function recommendSchemes(payload) {
  requireApi();
  return apiFetch("/api/dss/schemes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDssMetrics() {
  requireApi();
  return apiFetch("/api/dss/metrics");
}

export async function fetchDssBenchmark() {
  requireApi();
  return apiFetch("/api/dss/benchmark");
}

export async function fetchDssWhatIf(payload) {
  requireApi();
  return apiFetch("/api/dss/what-if", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDssReasons(payload) {
  requireApi();
  return apiFetch("/api/dss/reasons", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDssEta(payload) {
  requireApi();
  return apiFetch("/api/dss/eta", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDssTriage({ state, limit = 50 } = {}) {
  requireApi();
  const params = new URLSearchParams();
  if (state) params.set("state", state);
  if (limit) params.set("limit", String(limit));
  const q = params.toString() ? `?${params}` : "";
  return apiFetch(`/api/dss/triage${q}`);
}
