import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/api/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register:    (data: { email: string; password: string; full_name: string }) =>
    api.post("/api/auth/register", data),
  login:       (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  refresh:     (refresh_token: string) =>
    api.post("/api/auth/refresh", { refresh_token }),
  verifyEmail: (token: string) =>
    api.post(`/api/auth/verify-email?token=${token}`),
};

export const portfolioAPI = {
  list:     () => api.get("/api/portfolios"),
  get:      (id: string) => api.get(`/api/portfolios/${id}`),
  create:   (data: unknown) => api.post("/api/portfolios", data),
  update:   (id: string, data: unknown) => api.patch(`/api/portfolios/${id}`, data),
  delete:   (id: string) => api.delete(`/api/portfolios/${id}`),
  getDrift: (id: string) => api.get(`/api/portfolios/${id}/drift`),
};

export const rebalancingAPI = {
  list:         () => api.get("/api/rebalancing"),
  get:          (id: string) => api.get(`/api/rebalancing/${id}`),
  create:       (data: unknown) => api.post("/api/rebalancing", data),
  getCallData:  (id: string) => api.get(`/api/rebalancing/${id}/call-data`),
  confirmTx:    (id: string, tx_hash: string) =>
    api.post(`/api/rebalancing/${id}/confirm-tx`, { tx_hash }),
  pollResult:   (id: string) => api.post(`/api/rebalancing/${id}/poll-result`),
  getRationale: (id: string) => api.get(`/api/rebalancing/${id}/rationale`),
  exportPdf:    (id: string) =>
    api.get(`/api/rebalancing/${id}/export/pdf`, { responseType: "blob" }),
  exportCsv:    (id: string) =>
    api.get(`/api/rebalancing/${id}/export/csv`, { responseType: "blob" }),
};

export const userAPI = {
  me:        () => api.get("/api/users/me"),
  update:    (data: unknown) => api.patch("/api/users/me", data),
  wallet:    () => api.get("/api/users/me/wallet"),
  exportKey: (password: string) =>
    api.post("/api/users/me/wallet/export-key", { password }),
};

export const auditAPI = {
  events:     (params?: { limit?: number; event_type?: string }) =>
    api.get("/api/audit/events", { params }),
  compliance: () => api.get("/api/audit/compliance"),
};

export const adminAPI = {
  stats:      () => api.get("/api/admin/stats"),
  users:      () => api.get("/api/admin/users"),
  updateRole: (userId: string, role: string) =>
    api.patch(`/api/admin/users/${userId}/role?role=${role}`),
};
