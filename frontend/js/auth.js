/* ===========================================================
   FixCampus — Auth helpers
   =========================================================== */

function ccSaveSession(data) {
  localStorage.setItem("token", data.token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("name", data.name || "");
  localStorage.setItem("userId", data.id || "");
  localStorage.setItem("departmentId", data.department_id || "");
}

function ccLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("name");
  localStorage.removeItem("userId");
  localStorage.removeItem("departmentId");
  window.location.href = "login.html";
}

/* Call at the top of every dashboard page */
function ccRequireRole(expectedRole) {
  const role = localStorage.getItem("role");
  const token = localStorage.getItem("token");
  if (!token || role !== expectedRole) {
    window.location.href = "login.html";
  }
}

function ccFillUserBadge() {
  const nameEl = document.getElementById("sidebarName");
  const roleEl = document.getElementById("sidebarRole");
  if (nameEl) nameEl.textContent = localStorage.getItem("name") || "User";
  if (roleEl) roleEl.textContent = localStorage.getItem("role") || "";
}

/* ---------- login.html wiring ---------- */
function initLoginPage() {
  let selectedRole = "student";
  const tabs = document.querySelectorAll(".role-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      selectedRole = tab.dataset.role;
    });
  });

  const form = document.getElementById("loginForm");
  const msg = document.getElementById("loginMsg");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.className = "form-msg";
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "Signing in...";

    try {
      const data = await ccLogin(email, password, selectedRole);
      ccSaveSession(data);
      window.location.href = `${data.role}-dashboard.html`;
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "form-msg error";
      btn.disabled = false;
      btn.textContent = "Sign in";
    }
  });
}

/* ---------- register.html wiring ---------- */
function initRegisterPage() {
  let selectedRole = "student";
  const tabs = document.querySelectorAll(".role-tab");
  const sub = document.getElementById("registerSub");
  const deptField = document.getElementById("departmentField");
  const deptSelect = document.getElementById("regDepartment");

  const subText = {
    student: "Register as a student or faculty member to start reporting campus issues right away.",
    staff: "Register as department staff. Pick your department — your account will need admin approval before you can log in.",
  };

  async function loadDepartments() {
    try {
      const departments = await ccGetDepartments();
      deptSelect.innerHTML =
        `<option value="">Select your department</option>` +
        departments.map((d) => `<option value="${d.id}">${d.name}</option>`).join("");
    } catch (e) {
      deptSelect.innerHTML = `<option value="">Couldn't load departments — is the backend running?</option>`;
    }
  }
  loadDepartments();

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      selectedRole = tab.dataset.role;
      sub.textContent = subText[selectedRole];
      deptField.style.display = selectedRole === "staff" ? "block" : "none";
      deptSelect.required = selectedRole === "staff";
    });
  });

  const form = document.getElementById("registerForm");
  const msg = document.getElementById("registerMsg");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.className = "form-msg";
    const name = document.getElementById("regName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const confirm = document.getElementById("regConfirm").value;
    const department_id = deptSelect.value || null;
    const btn = form.querySelector("button[type=submit]");

    if (password !== confirm) {
      msg.textContent = "Passwords do not match.";
      msg.className = "form-msg error";
      return;
    }
    if (selectedRole === "staff" && !department_id) {
      msg.textContent = "Please select a department.";
      msg.className = "form-msg error";
      return;
    }

    btn.disabled = true;
    btn.textContent = "Creating account...";

    try {
      const data = await ccRegister({ name, email, password, role: selectedRole, department_id });

      if (data.pending) {
        msg.textContent = "Account created. It's now pending admin approval — you'll be able to log in once approved.";
        msg.className = "form-msg success";
        form.reset();
        btn.disabled = false;
        btn.textContent = "Create account";
        return;
      }

      ccSaveSession(data);
      window.location.href = `${data.role}-dashboard.html`;
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "form-msg error";
      btn.disabled = false;
      btn.textContent = "Create account";
    }
  });
}
