/* ===========================================================
   FixCampus — Staff dashboard
   =========================================================== */

ccRequireRole("staff");
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
// Staff can move a ticket through these — 'closed' only happens via the reporter's confirmation.
const NEXT_STATUSES = ["acknowledged", "in_progress", "resolved"];

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

async function loadAssigned() {
  // department-scoped by default (everything routed to my department)
  const complaints = await ccGetTickets({});
  const list = document.getElementById("complaintsList");

  document.getElementById("statAssigned").textContent = complaints.length;
  document.getElementById("statProgress").textContent = complaints.filter(c => c.status === "in_progress").length;
  document.getElementById("statDone").textContent = complaints.filter(c => ["resolved", "closed"].includes(c.status)).length;

  if (!complaints.length) {
    list.innerHTML = `<p class="empty-state">No complaints in your department's queue yet.</p>`;
    return;
  }

  list.innerHTML = complaints.map(c => `
    <div class="complaint-row" style="flex-wrap:wrap;">
      <div class="info">
        <h4>${c.title}</h4>
        <p>${c.description}</p>
        <div class="meta">${c.ticket_code} • ${c.location} • Priority: ${c.priority} • Submitted ${timeAgo(c.created_at)}${c.sla_breached ? " • <span style='color:#ff8080'>past SLA</span>" : ""}</div>
      </div>
      <span class="badge badge-${badgeClass(c.status)}">${STATUS_LABELS[c.status]}</span>
      ${["resolved", "closed"].includes(c.status) ? "" : `
        <select class="status-select" data-id="${c.id}">
          ${NEXT_STATUSES.map(s => `<option value="${s}" ${s === c.status ? "selected" : ""}>${STATUS_LABELS[s]}</option>`).join("")}
        </select>`}
    </div>
  `).join("");

  list.querySelectorAll(".status-select").forEach(sel => {
    sel.addEventListener("change", async (e) => {
      await ccUpdateTicketStatus(e.target.dataset.id, e.target.value);
      loadAssigned();
    });
  });
}

async function loadAvgResponse() {
  try {
    const stats = await ccGetStats();
    document.getElementById("statAvg").textContent = stats.avgResponseTime;
  } catch (e) { /* non-critical */ }
}

loadAssigned();
loadAvgResponse();
