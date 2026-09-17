/* ===========================================================
   FixCampus — Landing page logic
   =========================================================== */

async function loadStats() {
  try {
    const stats = await ccGetStats();
    document.getElementById("resolvedCount").textContent = stats.resolved + "+";
    document.getElementById("usersCount").textContent = stats.users + "+";
    document.getElementById("avgResponse").textContent = stats.avgResponseTime;
  } catch (e) {
    console.error("Failed to load stats", e);
  }
}

async function loadTestimonials() {
  try {
    const feedback = await ccGetFeedback();
    const grid = document.getElementById("testimonialsGrid");

    if (!feedback.length) {
      grid.innerHTML = `<p class="empty-state" style="grid-column:1/-1;">No feedback yet — be the first to resolve a ticket and leave a rating.</p>`;
      return;
    }

    grid.innerHTML = feedback
      .map((f) => {
        const initial = (f.user_name || "A").charAt(0).toUpperCase();
        const stars = "★".repeat(f.rating) + "☆".repeat(5 - f.rating);
        const date = new Date(f.created_at).toLocaleDateString("en-GB");
        return `
          <div class="testimonial-card">
            <div class="t-avatar">${initial}</div>
            <div class="t-name">${f.user_name || "Anonymous"}</div>
            <div class="t-role">FixCampus User</div>
            <div class="t-stars">${stars}</div>
            <div class="t-comment">"${f.comment}"</div>
            <div class="t-date">${date}</div>
          </div>`;
      })
      .join("");
  } catch (e) {
    console.error("Failed to load testimonials", e);
    document.getElementById("testimonialsGrid").innerHTML =
      `<p class="empty-state" style="grid-column:1/-1;">Couldn't load feedback right now.</p>`;
  }
}

function initThemeToggle() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
    btn.textContent = document.body.classList.contains("light-theme") ? "🌙" : "☀️";
  });
}

loadStats();
loadTestimonials();
initThemeToggle();
