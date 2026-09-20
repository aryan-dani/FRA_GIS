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

/**
 * Fetch claims (Firestore + synthetic by default).
 * @param {{ source?: string, limit?: number|string, state?: string, status?: string, q?: string }} [opts]
 */
export async function fetchClaims(opts = {}) {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  const params = new URLSearchParams();
  params.set("source", opts.source || "all");
  // Default 5000 keeps the UI responsive; pass limit: "all" for the full 125k set
  if (opts.limit !== undefined && opts.limit !== null) {
    params.set("limit", String(opts.limit));
  } else {
    params.set("limit", "5000");
  }
  if (opts.state) params.set("state", opts.state);
  if (opts.status) params.set("status", opts.status);
  if (opts.q) params.set("q", opts.q);
  if (opts.offset != null) params.set("offset", String(opts.offset));
  return apiFetch(`/api/claims?${params.toString()}`);
}

export async function fetchClaimById(claimId) {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  return apiFetch(`/api/claims/${encodeURIComponent(claimId)}`);
}

export async function createClaim(claimData) {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  const { entities, ...insertData } = claimData;
  return apiFetch("/api/claims", {
    method: "POST",
    body: JSON.stringify({
      ...insertData,
      latitude:
        insertData.latitude === ""
          ? null
          : Number(insertData.latitude) || insertData.latitude,
      longitude:
        insertData.longitude === ""
          ? null
          : Number(insertData.longitude) || insertData.longitude,
    }),
  });
}

export async function updateClaimStatus(claimId, status) {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  return apiFetch(`/api/claims/${encodeURIComponent(claimId)}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
}
