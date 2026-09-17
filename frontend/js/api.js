/* ===========================================================
   FixCampus — API wrapper
   Talks directly to the FastAPI + SQLite backend. No demo mode,
   no fake accounts, no fake reviews — everything shown in the
   UI is real data from your backend.
   =========================================================== */

const API_BASE = "http://localhost:8000/api";

async function apiRequest(endpoint, method = "GET", body = null, isFormData = false) {
  const token = localStorage.getItem("token");
  const headers = { ...(token && { Authorization: `Bearer ${token}` }) };
  if (!isFormData) headers["Content-Type"] = "application/json";

  let res;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers,
      body: body ? (isFormData ? body : JSON.stringify(body)) : null,
    });
  } catch (e) {
    throw new Error("Can't reach the FixCampus server. Make sure the backend is running on http://localhost:8000.");
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || `Request failed (${res.status})`);
  return data;
}

/* ---- departments ---- */
async function ccGetDepartments() {
  return apiRequest("/departments");
}

/* ---- auth ---- */
async function ccLogin(email, password, role) {
  return apiRequest("/auth/login", "POST", { email, password, role });
}

async function ccRegister({ name, email, password, role, department_id }) {
  return apiRequest("/auth/register", "POST", { name, email, password, role, department_id });
}

/* ---- tickets ---- */
async function ccGetTickets(filter = {}) {
  const qs = new URLSearchParams(filter).toString();
  return apiRequest(`/tickets${qs ? "?" + qs : ""}`);
}

async function ccGetTicket(id) {
  return apiRequest(`/tickets/${id}`);
}

async function ccCreateTicket({ title, category, location, description }) {
  return apiRequest("/tickets", "POST", { title, category, location, description });
}

async function ccUpdateTicketStatus(id, status, note) {
  return apiRequest(`/tickets/${id}/status`, "PATCH", { status, note });
}

async function ccAssignTicket(id, staffId) {
  return apiRequest(`/tickets/${id}/assign`, "PATCH", { assigned_to: staffId });
}

async function ccConfirmTicket(id, confirmed, rating, comment) {
  return apiRequest(`/tickets/${id}/confirm`, "POST", { confirmed, rating, comment });
}

/* ---- users / staff approval (admin) ---- */
async function ccGetStaffList(departmentId) {
  const params = { role: "staff", status: "active" };
  if (departmentId) params.department_id = departmentId;
  return apiRequest(`/users?${new URLSearchParams(params).toString()}`);
}

async function ccGetPendingStaff() {
  return apiRequest(`/users?${new URLSearchParams({ role: "staff", status: "pending" }).toString()}`);
}

async function ccApproveStaff(id) {
  return apiRequest(`/users/${id}/approve`, "PATCH");
}

async function ccRejectStaff(id) {
  return apiRequest(`/users/${id}/reject`, "PATCH");
}

/* ---- feedback & stats ---- */
async function ccGetFeedback() {
  return apiRequest("/feedback");
}

async function ccGetStats() {
  return apiRequest("/stats/overview");
}

async function ccGetDepartmentStats() {
  return apiRequest("/stats/departments");
}
