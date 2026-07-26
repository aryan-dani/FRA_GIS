const API_URL = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

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

export async function fetchClaims() {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  return apiFetch("/api/claims");
}

export async function fetchClaimById(claimId) {
  if (!API_URL) {
    throw new Error("REACT_APP_API_URL is not configured.");
  }
  return apiFetch(`/api/claims/${claimId}`);
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
  return apiFetch(`/api/claims/${claimId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
}
