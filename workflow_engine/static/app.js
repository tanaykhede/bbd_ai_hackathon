// Simple SPA logic for Workflow Admin
const state = {
  token: null,
  user: null,
};

const api = {
  baseUrl: "",
  headers() {
    const h = { "Content-Type": "application/json" };
    if (state.token) h["Authorization"] = `Bearer ${state.token}`;
    return h;
  },
  async get(path) {
    const res = await fetch(`${this.baseUrl}${path}`, { headers: this.headers() });
    if (!res.ok) throw await api._err(res);
    return res.json();
  },
  async post(path, body, isForm = false) {
    const opts = {
      method: "POST",
      headers: isForm ? {} : this.headers(),
      body: isForm ? body : JSON.stringify(body),
    };
    if (isForm) {
      // For form-encoded login, set header explicitly
      opts.headers["Content-Type"] = "application/x-www-form-urlencoded";
    }
    if (!isForm && state.token) {
      opts.headers["Authorization"] = `Bearer ${state.token}`;
    }
    const res = await fetch(`${this.baseUrl}${path}`, opts);
    if (!res.ok) throw await api._err(res);
    return res.json();
  },
  async put(path, body) {
    const opts = {
      method: "PUT",
      headers: this.headers(),
      body: JSON.stringify(body),
    };
    const res = await fetch(`${this.baseUrl}${path}`, opts);
    if (!res.ok) throw await api._err(res);
    return res.json();
  },
  _err: async (res) => {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j && j.detail) msg += ` - ${Array.isArray(j.detail) ? j.detail.map(x => x.msg).join(", ") : j.detail}`;
    } catch {}
    return new Error(msg);
  }
};

function notify(msg, type = "info") {
  const el = document.getElementById("messages");
  el.textContent = msg;
  el.className = `message ${type}`;
  setTimeout(() => { el.textContent = ""; el.className = "message"; }, 4000);
}

function setAuthStatus() {
  const status = document.getElementById("auth-status");
  const logout = document.getElementById("logout-btn");
  if (state.user) {
    status.textContent = `Logged in as ${state.user.username} (${state.user.role})`;
    logout.style.display = "inline-block";
  } else {
    status.textContent = "Not logged in";
    logout.style.display = "none";
  }
}

async function login(username, password) {
  const body = new URLSearchParams();
  body.append("grant_type", "password"); // ensure compatibility with OAuth2PasswordRequestForm
  body.append("username", username);
  body.append("password", password);
  try {
    const resp = await api.post("/auth/token", body, true);
    state.token = resp.access_token;
    const me = await api.get("/auth/me");
    state.user = me;
    setAuthStatus();
    notify("Login successful", "success");
    await refreshAll();
  } catch (e) {
    notify(`Login failed: ${e.message}`, "error");
  }
}

async function register(username, password) {
  try {
    // role is required by the API model; server decides actual role (first user -> admin)
    await api.post("/auth/register", { username, password, role: "user" });
    notify("Registration successful, logging in...", "success");
    await login(username, password);
  } catch (e) {
    notify(`Registration failed: ${e.message}`, "error");
  }
}

function logout() {
  state.token = null;
  state.user = null;
  setAuthStatus();
  notify("Logged out", "success");
}

function bindAuth() {
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const u = document.getElementById("username").value.trim();
    const p = document.getElementById("password").value;
    await login(u, p);
  });

  document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const u = document.getElementById("reg-username").value.trim();
    const p = document.getElementById("reg-password").value;
    await register(u, p);
  });

  document.getElementById("logout-btn").addEventListener("click", logout);
}

function bindTabs() {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      panels.forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.target);
      if (target) target.classList.add("active");
    });
  });
}

async function refreshAll() {
  await Promise.all([
    loadStatuses(),
    loadProcessTypes(),
    loadProcessDataTypes(),
    loadProcessDefinitions(),
    loadTasks(),
    loadTaskRules(),
  ]);
}

// Render helpers
function renderList(elId, items, mapFn) {
  const el = document.getElementById(elId);
  if (!items || items.length === 0) {
    el.innerHTML = "<div class='empty'>No records</div>";
    return;
  }
  el.innerHTML = items.map(mapFn).join("");
}

function renderDetail(elId, item, mapFn) {
  const el = document.getElementById(elId);
  if (!item) {
    el.innerHTML = "<div class='empty'>Not found</div>";
    return;
  }
  el.innerHTML = mapFn(item);
}

// Loaders
async function loadStatuses() {
  try {
    const items = await api.get("/statuses");
    renderList("status-list", items, s => `<div class="item">#${s.statusno} - ${s.description}</div>`);
  } catch (e) { notify(`Failed to load statuses: ${e.message}`, "error"); }
}

async function loadProcessTypes() {
  try {
    const items = await api.get("/process-types");
    renderList("process-type-list", items, i => `<div class="item">#${i.process_type_no} - ${i.description}</div>`);
  } catch (e) { notify(`Failed to load process types: ${e.message}`, "error"); }
}

async function loadProcessDataTypes() {
  try {
    const items = await api.get("/process-data-types");
    renderList("process-data-type-list", items, i => `<div class="item">#${i.process_data_type_no} - ${i.description}</div>`);
  } catch (e) { notify(`Failed to load process data types: ${e.message}`, "error"); }
}

async function loadProcessDefinitions() {
  try {
    const items = await api.get("/process-definitions");
    renderList("process-definition-list", items, i => {
      return `<div class="item">
        #${i.process_definition_no}
        type=${i.process_type_no}
        start=${i.start_task_no}
        v=${i.version}
        active=${i.is_active}
        user=${i.usrid}
        ts=${i.tmstamp}
      </div>`;
    });
  } catch (e) { notify(`Failed to load process definitions: ${e.message}`, "error"); }
}

async function loadTasks() {
  try {
    const items = await api.get("/tasks");
    renderList("task-list", items, i => `<div class="item">#${i.taskno} (pd ${i.process_definition_no}) - ${i.description} [${i.reference ?? ""}]</div>`);
  } catch (e) { notify(`Failed to load tasks: ${e.message}`, "error"); }
}

async function loadTaskRules() {
  try {
    const items = await api.get("/task-rules");
    renderList(
      "task-rule-list",
      items,
      i => `<div class="item">#${i.taskruleno} · task ${i.taskno} - rule "${i.rule}" -> next ${i.next_task_no ?? "None"}</div>`
    );
  } catch (e) { notify(`Failed to load task rules: ${e.message}`, "error"); }
}

// Create + Retrieve handlers
function bindForms() {
  // Create
  document.getElementById("status-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const description = document.getElementById("status-description").value.trim();
    try {
      await api.post("/statuses/", { description });
      notify("Status created", "success");
      document.getElementById("status-description").value = "";
      await loadStatuses();
    } catch (err) { notify(`Create status failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-type-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const description = document.getElementById("process-type-description").value.trim();
    try {
      await api.post("/process-types/", { description });
      notify("Process type created", "success");
      document.getElementById("process-type-description").value = "";
      await loadProcessTypes();
    } catch (err) { notify(`Create process type failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-data-type-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const description = document.getElementById("process-data-type-description").value.trim();
    try {
      await api.post("/process-data-types/", { description });
      notify("Process data type created", "success");
      document.getElementById("process-data-type-description").value = "";
      await loadProcessDataTypes();
    } catch (err) { notify(`Create process data type failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-definition-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const process_type_no = parseInt(document.getElementById("pd-process-type-no").value, 10);
    const version = document.getElementById("pd-version").value.trim();
    const is_active = document.getElementById("pd-is-active").checked;
    const start_task_description = document.getElementById("pd-start-task-description").value.trim();
    try {
      await api.post("/process-definitions/", {
        process_type_no, version, is_active, start_task_description
      });
      notify("Process definition created (with start task and default rule)", "success");
      document.getElementById("pd-start-task-description").value = "";
      await loadProcessDefinitions();
    } catch (err) { notify(`Create process definition failed: ${err.message}`, "error"); }
  });

  document.getElementById("task-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const process_definition_no = parseInt(document.getElementById("task-process-definition-no").value, 10);
    const description = document.getElementById("task-description").value.trim();
    const reference = document.getElementById("task-reference").value.trim();
    try {
      await api.post("/tasks/", { process_definition_no, description, reference });
      notify("Task created", "success");
      document.getElementById("task-description").value = "";
      document.getElementById("task-reference").value = "";
      await loadTasks();
    } catch (err) { notify(`Create task failed: ${err.message}`, "error"); }
  });

  document.getElementById("task-rule-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const taskno = parseInt(document.getElementById("tr-taskno").value, 10);
    const rule = document.getElementById("tr-rule").value.trim();
    const nextTaskEl = document.getElementById("tr-next-task-no");
    const next_task_no = nextTaskEl.value ? parseInt(nextTaskEl.value, 10) : null;
    try {
      await api.post("/task-rules/", { taskno, rule, next_task_no });
      notify("Task rule created", "success");
      nextTaskEl.value = "";
      document.getElementById("tr-rule").value = "";
      await loadTaskRules();
    } catch (err) { notify(`Create task rule failed: ${err.message}`, "error"); }
  });

  // Update Status
  document.getElementById("status-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("status-upd-id").value, 10);
    const description = document.getElementById("status-upd-description").value.trim();
    try {
      await api.put(`/statuses/${id}`, { description });
      notify("Status updated", "success");
      await loadStatuses();
    } catch (err) { notify(`Update status failed: ${err.message}`, "error"); }
  });

  // Update Process Type
  document.getElementById("process-type-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("process-type-upd-id").value, 10);
    const description = document.getElementById("process-type-upd-description").value.trim();
    const body = {};
    if (description) body.description = description;
    try {
      await api.put(`/process-types/${id}`, body);
      notify("Process type updated", "success");
      await loadProcessTypes();
    } catch (err) { notify(`Update process type failed: ${err.message}`, "error"); }
  });

  // Update Process Data Type
  document.getElementById("process-data-type-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("process-data-type-upd-id").value, 10);
    const description = document.getElementById("process-data-type-upd-description").value.trim();
    const body = {};
    if (description) body.description = description;
    try {
      await api.put(`/process-data-types/${id}`, body);
      notify("Process data type updated", "success");
      await loadProcessDataTypes();
    } catch (err) { notify(`Update process data type failed: ${err.message}`, "error"); }
  });

  // Update Task
  document.getElementById("task-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("task-upd-id").value, 10);
    const pd = document.getElementById("task-upd-process-definition-no").value;
    const desc = document.getElementById("task-upd-description").value.trim();
    const ref = document.getElementById("task-upd-reference").value.trim();
    const body = {};
    if (pd) body.process_definition_no = parseInt(pd, 10);
    if (desc) body.description = desc;
    if (ref) body.reference = ref;
    try {
      await api.put(`/tasks/${id}`, body);
      notify("Task updated", "success");
      await loadTasks();
    } catch (err) { notify(`Update task failed: ${err.message}`, "error"); }
  });

  // Update Task Rule
  document.getElementById("task-rule-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    // Backward-compatible: reuse the existing field to capture the Task Rule ID (taskruleno)
    const id = parseInt(document.getElementById("tr-upd-taskno").value, 10);
    // 'tr-upd-rule' is no longer required when updating by ID
    const next = document.getElementById("tr-upd-next-task-no").value;
    const body = {};
    if (next) body.next_task_no = parseInt(next, 10);
    try {
      await api.put(`/task-rules/${id}`, body);
      notify("Task rule updated", "success");
      await loadTaskRules();
    } catch (err) { notify(`Update task rule failed: ${err.message}`, "error"); }
  });

  // Retrieve
  document.getElementById("status-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("status-id").value, 10);
    try {
      const item = await api.get(`/statuses/${id}`);
      renderDetail("status-detail", item, s => `<div class="item">#${s.statusno} - ${s.description}</div>`);
    } catch (err) { notify(`Get status failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-type-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("process-type-id").value, 10);
    try {
      const item = await api.get(`/process-types/${id}`);
      renderDetail("process-type-detail", item, i => `<div class="item">#${i.process_type_no} - ${i.description}</div>`);
    } catch (err) { notify(`Get process type failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-data-type-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("process-data-type-id").value, 10);
    try {
      const item = await api.get(`/process-data-types/${id}`);
      renderDetail("process-data-type-detail", item, i => `<div class="item">#${i.process_data_type_no} - ${i.description}</div>`);
    } catch (err) { notify(`Get process data type failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-definition-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("process-definition-id").value, 10);
    try {
      const i = await api.get(`/process-definitions/${id}`);
      renderDetail("process-definition-detail", i, i => {
        return `<div class="item">
          #${i.process_definition_no}
          type=${i.process_type_no}
          start=${i.start_task_no}
          v=${i.version}
          active=${i.is_active}
          user=${i.usrid}
          ts=${i.tmstamp}
        </div>`;
      });
    } catch (err) { notify(`Get process definition failed: ${err.message}`, "error"); }
  });

  document.getElementById("process-definition-update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("pd-upd-id").value, 10);
    const body = {};
    const ptype = document.getElementById("pd-upd-process-type-no").value;
    const startno = document.getElementById("pd-upd-start-task-no").value;
    const version = document.getElementById("pd-upd-version").value.trim();
    const isActiveChecked = document.getElementById("pd-upd-is-active").checked;

    if (ptype) body.process_type_no = parseInt(ptype, 10);
    if (startno) body.start_task_no = parseInt(startno, 10);
    if (version) body.version = version;
    if (isActiveChecked) body.is_active = true; // leave unset to ignore; only set true when checked

    try {
      await api.put(`/process-definitions/${id}`, body);
      notify("Process definition updated", "success");
      await loadProcessDefinitions();
    } catch (err) {
      notify(`Update process definition failed: ${err.message}`, "error");
    }
  });

  document.getElementById("task-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = parseInt(document.getElementById("task-id").value, 10);
    try {
      const item = await api.get(`/tasks/${id}`);
      renderDetail("task-detail", item, i => `<div class="item">#${i.taskno} (pd ${i.process_definition_no}) - ${i.description} [${i.reference ?? ""}]</div>`);
    } catch (err) { notify(`Get task failed: ${err.message}`, "error"); }
  });

  document.getElementById("task-rule-get-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    // Use the ID (taskruleno); reuse the existing field for compatibility
    const id = parseInt(document.getElementById("tr-get-taskno").value, 10);
    try {
      const item = await api.get(`/task-rules/${id}`);
      renderDetail(
        "task-rule-detail",
        item,
        i => `<div class="item">#${i.taskruleno} · task ${i.taskno} - rule "${i.rule}" -> next ${i.next_task_no ?? "None"}</div>`
      );
    } catch (err) { notify(`Get task rule failed: ${err.message}`, "error"); }
  });
}

window.addEventListener("DOMContentLoaded", () => {
  bindAuth();
  bindTabs();
  bindForms();
  setAuthStatus();
});
