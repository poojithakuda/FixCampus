/* ===========================================================
   FixCampus — Admin dashboard
   =========================================================== */

ccRequireRole("admin");
ccFillUserBadge();

document.getElementById("logoutBtn").addEventListener("click", ccLogout);
document.getElementById("sidebarLogout").addEventListener("click", (e) => { e.preventDefault(); ccLogout(); });

const STATUS_LABELS = {
  reported: "Reported",
  acknowledged: "Acknowledged",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr + "Z").getTime();
  const hrs = Math.floor(diff / 3600000);
  if (hrs < 1) return "just now";
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function badgeClass(status) {
  if (status === "reported") return "submitted";
  if (status === "acknowledged") return "assigned";
  if (status === "closed") return "resolved";
  return status;
}

async function loadPendingStaff() {
  const pending = await ccGetPendingStaff();
  const list = document.getElementById("pendingStaffList");

  if (!pending.length) {
    list.innerHTML = `<p class="empty-state">No staff accounts waiting for approval.</p>`;
    return;
  }

  list.innerHTML = pending.map(u => `
    <div class="complaint-row">
      <div class="info">
        <h4>${u.name}</h4>
        <p>${u.email}</p>
        <div class="meta">Requested staff access</div>
      </div>
      <button class="btn btn-primary" data-approve="${u.id}" style="padding:8px 16px; font-size:0.82rem;">Approve</button>
      <button class="btn btn-outline" data-reject="${u.id}" style="padding:8px 16px; font-size:0.82rem;">Reject</button>
    </div>
  `).join("");

  list.querySelectorAll("[data-approve]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await ccApproveStaff(btn.dataset.approve);
      loadPendingStaff();
      loadAll();
    });
  });
  list.querySelectorAll("[data-reject]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await ccRejectStaff(btn.dataset.reject);
      loadPendingStaff();
    });
  });
}

async function loadDepartmentBreakdown() {
  const rows = await ccGetDepartmentStats();
  const el = document.getElementById("departmentBreakdown");
  el.innerHTML = rows.map(d => `
    <div class="mini-stat">
      <div class="num">${d.total}</div>
      <div class="lbl">${d.name} — ${d.open} open, ${d.resolved} resolved</div>
    </div>
  `).join("");
}

async function loadAll() {
  const [tickets, stats, allStaff] = await Promise.all([
    ccGetTickets(),
    ccGetStats(),
    ccGetStaffList(),
  ]);

  const list = document.getElementById("complaintsList");
  document.getElementById("statTotal").textContent = tickets.length;
  document.getElementById("statUnassigned").textContent = tickets.filter(c => !c.assigned_to).length;
  document.getElementById("statResolved").textContent = tickets.filter(c => ["resolved", "closed"].includes(c.status)).length;
  document.getElementById("statUsers").textContent = stats.users;

  if (!tickets.length) {
    list.innerHTML = `<p class="empty-state">No complaints have been submitted yet.</p>`;
    return;
  }

  list.innerHTML = tickets.map(c => {
    const deptStaff = allStaff.filter(s => s.department_id === c.department_id);
    return `
    <div class="complaint-row" style="flex-wrap:wrap;">
      <div class="info">
        <h4>${c.title}</h4>
        <p>${c.description}</p>
        <div class="meta">${c.ticket_code} • ${c.location} • ${c.category} • Priority: ${c.priority} • Submitted ${timeAgo(c.created_at)}</div>
      </div>
      <span class="badge badge-${badgeClass(c.status)}">${STATUS_LABELS[c.status]}</span>
      <select class="status-select assign-select" data-id="${c.id}" ${["resolved","closed"].includes(c.status) ? "disabled" : ""}>
        <option value="">${c.assigned_to ? "Reassign..." : "Assign staff..."}</option>
        ${deptStaff.map(s => `<option value="${s.id}" ${c.assigned_to === s.id ? "selected" : ""}>${s.name}</option>`).join("")}
      </select>
    </div>
  `;
  }).join("");

  list.querySelectorAll(".assign-select").forEach(sel => {
    sel.addEventListener("change", async (e) => {
      if (!e.target.value) return;
      await ccAssignTicket(e.target.dataset.id, e.target.value);
      loadAll();
    });
  });
}

loadAll();
loadPendingStaff();
loadDepartmentBreakdown();
