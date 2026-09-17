/* ===========================================================
   FixCampus — Student dashboard
   =========================================================== */

ccRequireRole("student");
ccFillUserBadge();

document.getElementById("logoutBtn").addEventListener("click", ccLogout);
document.getElementById("sidebarLogout").addEventListener("click", (e) => { e.preventDefault(); ccLogout(); });

const STATUS_LABELS = {
  reported: "Reported",
  acknowledged: "Acknowledged",
  in_progress: "In Progress",
  resolved: "Resolved — awaiting your confirmation",
  closed: "Closed",
};

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr + "Z").getTime();
  const hrs = Math.floor(diff / 3600000);
  if (hrs < 1) return "just now";
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

async function loadCategories() {
  const select = document.getElementById("cCategory");
  try {
    const departments = await ccGetDepartments();
    select.innerHTML =
      `<option value="">Select a category</option>` +
      departments.map((d) => `<option value="${d.category}">${d.name} (${d.category})</option>`).join("");
  } catch (e) {
    select.innerHTML = `<option value="">Couldn't load categories — is the backend running?</option>`;
  }
}

async function loadMyComplaints() {
  const complaints = await ccGetTickets({});
  const list = document.getElementById("complaintsList");

  document.getElementById("statTotal").textContent = complaints.length;
  document.getElementById("statOpen").textContent = complaints.filter(c => ["acknowledged", "in_progress"].includes(c.status)).length;
  document.getElementById("statResolved").textContent = complaints.filter(c => c.status === "closed").length;

  if (!complaints.length) {
    list.innerHTML = `<p class="empty-state">No complaints yet. Submit your first one above.</p>`;
    return;
  }

  list.innerHTML = complaints.map(c => `
    <div class="complaint-row" style="flex-wrap:wrap;">
      <div class="info">
        <h4>${c.title}</h4>
        <p>${c.description}</p>
        <div class="meta">${c.ticket_code} • ${c.location} • Submitted ${timeAgo(c.created_at)}${c.sla_breached ? " • <span style='color:#ff8080'>past SLA</span>" : ""}</div>
      </div>
      <span class="badge badge-${c.status === "reported" ? "submitted" : c.status === "acknowledged" ? "assigned" : c.status === "closed" ? "resolved" : c.status}">${STATUS_LABELS[c.status]}</span>
      ${c.status === "resolved" ? `
        <div style="display:flex; gap:8px;">
          <button class="btn btn-primary" data-confirm="${c.id}" style="padding:8px 14px; font-size:0.8rem;">Confirm fixed</button>
          <button class="btn btn-outline" data-reopen="${c.id}" style="padding:8px 14px; font-size:0.8rem;">Not fixed</button>
        </div>` : ""}
    </div>
  `).join("");

  list.querySelectorAll("[data-confirm]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const rating = prompt("Rate the resolution 1-5 (optional, press cancel to skip):");
      const comment = rating ? prompt("Any comment? (optional)") : null;
      await ccConfirmTicket(btn.dataset.confirm, true, rating ? Number(rating) : null, comment);
      loadMyComplaints();
    });
  });
  list.querySelectorAll("[data-reopen]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await ccConfirmTicket(btn.dataset.reopen, false);
      loadMyComplaints();
    });
  });
}

document.getElementById("complaintForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("submitMsg");
  msg.className = "form-msg";

  const title = document.getElementById("cTitle").value.trim();
  const category = document.getElementById("cCategory").value;
  const location = document.getElementById("cLocation").value.trim();
  const description = document.getElementById("cDescription").value.trim();

  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Submitting...";

  try {
    const result = await ccCreateTicket({ title, category, location, description });
    msg.textContent = result.duplicate_of_code
      ? `Submitted as ${result.ticket_code} — matched as a possible duplicate of ${result.duplicate_of_code} at the same location.`
      : `Submitted successfully as ${result.ticket_code}.`;
    msg.className = "form-msg success";
    e.target.reset();
    loadMyComplaints();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "form-msg error";
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit complaint";
  }
});

loadCategories();
loadMyComplaints();
