const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const message = data?.detail || data?.message || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  analyze: (payload) => request("/analyze", { method: "POST", body: JSON.stringify(payload) }),
  history: (limit = 20) => request(`/history?limit=${encodeURIComponent(limit)}`),
  historyDetail: (id) => request(`/history/${id}`),
  deleteHistory: (id) => request(`/history/${id}`, { method: "DELETE" }),
  ragStatus: () => request("/rag/status"),
};

export { API_BASE };
