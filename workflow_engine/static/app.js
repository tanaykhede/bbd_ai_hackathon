// Simple SPA logic for Workflow Admin
const state = {
  token: null,
  user: null,
  userPortal: { currentCase: null, currentStep: null, processData: [] },
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
  if (!el) {
    // Fallback to console if messages container is not present
    if (type === "error") console.error(msg);
    else console.log(msg);
    return;
  }
  el.textContent = msg;
  el.className = `message ${type}`;
  clearTimeout(notify._clearTimer);
  notify._clearTimer = setTimeout(() => { el.textContent = ""; el.className = "message"; }, 4000);
}

function setAuthStatus() {
  const status = document.getElementById("auth-status");
  const logout = document.getElementById("logout-btn");
  if (!status || !logout) return;
  if (state.user) {
    status.textContent = `Logged in as ${state.user.username} (${state.user.role ?? ""})`;
    logout.style.display = "inline-block";
  } else {
    status.textContent = "Not logged in";
    logout.style.display = "none";
  }

  // Role-based UI adjustments
  const roles = Array.isArray(state.user?.roles) ? state.user.roles : [state.user?.role].filter(Boolean);
  const isAdmin = roles.includes("admin");
  const isUserOnly = roles.includes("user") && !isAdmin;

  const headerTitle = document.querySelector("header h1");
  if (isUserOnly) {
    // User console
    document.title = "Workflow User Console";
    if (headerTitle) headerTitle.textContent = "Workflow User Console";

    // Show only the User Portal tab and panel
    const tabButtons = document.querySelectorAll(".tabs .tab");
    const panels = document.querySelectorAll(".panel");
    tabButtons.forEach(btn => {
      const show = btn.dataset.target === "user-portal";
      btn.style.display = show ? "inline-block" : "none";
      btn.classList.toggle("active", show);
    });
    panels.forEach(p => {
      p.classList.toggle("active", p.id === "user-portal");
    });
  } else {
    // Admin or logged out: admin console view
    document.title = "Workflow Admin";
    if (headerTitle) headerTitle.textContent = "Workflow Admin Console";
    const tabButtons = document.querySelectorAll(".tabs .tab");
    tabButtons.forEach(btn => { btn.style.display = "inline-block"; });
    // Keep current active tab/panel as-is
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
    // Clear fields/lists and then (optionally) load data based on role
    clearFieldsAndLists();
    await loadUserPortal(); // ensure user portal data loads for non-admin users
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
    // Clear registration fields
    const ru = document.getElementById("reg-username"); if (ru) ru.value = "";
    const rp = document.getElementById("reg-password"); if (rp) rp.value = "";
    await login(username, password);
  } catch (e) {
    notify(`Registration failed: ${e.message}`, "error");
  }
}

function logout() {
  state.token = null;
  state.user = null;
  setAuthStatus();
  clearFieldsAndLists();
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
    renderList("task-rule-list", items, i => `<div class="item">#${i.taskruleno} task ${i.taskno} - rule "${i.rule}" -> next ${i.next_task_no ?? "None"}</div>`);
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
    const next_task_no = nextTaskEl && nextTaskEl.value ? parseInt(nextTaskEl.value, 10) : null;
    try {
      await api.post("/task-rules/", { taskno, rule, next_task_no });
      notify("Task rule created", "success");
      if (nextTaskEl) nextTaskEl.value = "";
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
    const form = e.currentTarget;
    const tasknoStr = form.querySelector("#tr-upd-taskno")?.value ?? "";
    const ruleInputVal = form.querySelector("#tr-upd-rule")?.value?.trim() ?? "";
    const rule = encodeURIComponent(ruleInputVal);
    const newRule = ruleInputVal;
    const nextStr = form.querySelector("#tr-upd-next-task-no")?.value ?? "";
    const body = {};
    if (newRule) body.rule = newRule;
    if (nextStr) body.next_task_no = parseInt(nextStr, 10);
    try {
      await api.put(`/task-rules/${parseInt(tasknoStr, 10)}/${rule}`, body);
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
    const taskno = parseInt(document.getElementById("tr-get-taskno").value, 10);
    const rule = encodeURIComponent(document.getElementById("tr-get-rule").value.trim());
    try {
      const item = await api.get(`/task-rules/${taskno}/${rule}`);
      renderDetail("task-rule-detail", item, i => `<div class="item">task ${i.taskno} - rule "${i.rule}" -> next ${i.next_task_no ?? "None"}</div>`);
    } catch (err) { notify(`Get task rule failed: ${err.message}`, "error"); }
  });
}

// User Portal logic
function renderUserCurrent() {
  const wrap = document.getElementById("user-current");
  if (!wrap) return;
  const c = state.userPortal.currentCase;
  const s = state.userPortal.currentStep;
  if (!c) {
    wrap.innerHTML = "<div class='empty'>No case selected yet</div>";
    return;
  }
  const procno = s ? s.processno : "N/A";
  const stepno = s ? s.stepno : "N/A";
  const taskno = s ? s.taskno : "N/A";
  wrap.innerHTML = `
    <div class="item">
      <strong>Case #${c.caseno}</strong> (client_id=${c.client_id}, client_type=${c.client_type})
      <br/>Process: ${procno}, Current Step: ${stepno}, Task: ${taskno}
    </div>
  `;
}

async function loadUserProcessTypes() {
  const sel = document.getElementById("user-process-type-no");
  if (!sel) return;
  try {
    const items = await api.get("/process-types");
    sel.innerHTML = `<option value="">Select Process Type</option>` + items.map(pt =>
      `<option value="${pt.process_type_no}">${pt.process_type_no} - ${pt.description}</option>`
    ).join("");
  } catch (e) {
    notify(`Failed to load process types: ${e.message}`, "error");
  }
}

async function loadUserProcessDataTypes() {
  const selAdd = document.getElementById("user-pd-type");
  const selEdit = document.getElementById("user-pd-edit-type");
  try {
    const items = await api.get("/process-data-types");
    const html = `<option value="">Select Process Data Type</option>` + items.map(dt =>
      `<option value="${dt.process_data_type_no}">${dt.process_data_type_no} - ${dt.description}</option>`
    ).join("");
    if (selAdd) selAdd.innerHTML = html;
    if (selEdit) selEdit.innerHTML = html;
  } catch (e) {
    notify(`Failed to load process data types: ${e.message}`, "error");
  }
}

async function loadCaseProcessData(caseNo) {
  const listEl = document.getElementById("user-procdata-list");
  if (!listEl || !caseNo) return;
  try {
    const items = await api.get(`/cases/${caseNo}/process-data`);
    state.userPortal.processData = items || [];
    if (!items || items.length === 0) {
      listEl.innerHTML = "<div class='empty'>No process data</div>";
      return;
    }
    listEl.innerHTML = items.map(i => `
      <div class="item">
        #${i.process_data_no} &middot; type=${i.process_data_type_no} &middot; ${i.fieldname} = ${i.value}
        <div><button class="secondary" data-edit-pdno="${i.process_data_no}">Edit</button></div>
      </div>
    `).join("");
    listEl.querySelectorAll("button[data-edit-pdno]").forEach(btn => {
      btn.addEventListener("click", () => {
        const pdno = parseInt(btn.getAttribute("data-edit-pdno"), 10);
        const pd = state.userPortal.processData.find(x => x.process_data_no === pdno);
        if (pd) populateEditProcessDataForm(pd);
      });
    });
  } catch (e) {
    notify(`Failed to load case data: ${e.message}`, "error");
  }
}

function populateEditProcessDataForm(pd) {
  const idEl = document.getElementById("user-pd-edit-id");
  const typeEl = document.getElementById("user-pd-edit-type");
  const fieldEl = document.getElementById("user-pd-edit-field");
  const valueEl = document.getElementById("user-pd-edit-value");
  if (idEl) idEl.value = pd.process_data_no;
  if (typeEl) typeEl.value = String(pd.process_data_type_no);
  if (fieldEl) fieldEl.value = pd.fieldname || "";
  if (valueEl) valueEl.value = pd.value || "";
}

async function loadCaseSteps(caseNo) {
  const listEl = document.getElementById("user-steps-list");
  if (!listEl || !caseNo) return;
  try {
    const items = await api.get(`/cases/${caseNo}/steps`);
    if (!items || items.length === 0) {
      listEl.innerHTML = "<div class='empty'>No steps</div>";
      return;
    }
    listEl.innerHTML = items.map(s => `
      <div class="item">
        Step #${s.stepno} &middot; Task ${s.taskno} &middot; Status ${s.status_no}
        <br/>Started: ${s.date_started} ${s.date_ended ? `&middot; Ended: ${s.date_ended}` : ""}
      </div>
    `).join("");
  } catch (e) {
    notify(`Failed to load steps: ${e.message}`, "error");
  }
}

// Helpers for searching/selecting cases
async function listMyCases() {
  return api.get("/cases");
}

function renderSearchResults(items) {
  const el = document.getElementById("user-search-results");
  if (!el) return;
  if (!items || items.length === 0) {
    el.innerHTML = "<div class='empty'>No cases found</div>";
    return;
  }
  el.innerHTML = items.map(c => `
    <div class="item">
      <div>
        <strong>Case #${c.caseno}</strong> &middot; client_id=${c.client_id} &middot; client_type=${c.client_type}
      </div>
      <button class="secondary" data-select-caseno="${c.caseno}">Select</button>
    </div>
  `).join("");
  // Bind select buttons
  el.querySelectorAll("button[data-select-caseno]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const caseno = parseInt(btn.getAttribute("data-select-caseno"), 10);
      const target = items.find(i => i.caseno === caseno);
      if (target) {
        await selectCase(target);
      }
    });
  });
}

async function selectCase(c) {
  state.userPortal.currentCase = c;
  notify(`Selected case #${c.caseno}`, "success");
  await refreshUserCurrent();
  await loadCaseProcessData(c.caseno);
  await loadCaseSteps(c.caseno);
}

function updateProcessDataFormEnabled() {
  const addForm = document.getElementById("user-procdata-form");
  const editForm = document.getElementById("user-procdata-edit-form");
  const info = document.getElementById("user-procdata-edit-info");
  const disabled = !state.userPortal.currentStep; // enable only when a busy step exists
  if (addForm) {
    addForm.querySelectorAll("input, select, button[type='submit']").forEach(el => {
      el.disabled = disabled;
    });
  }
  if (editForm) {
    editForm.querySelectorAll("input, select, button[type='submit']").forEach(el => {
      el.disabled = disabled;
    });
  }
  if (info) {
    if (disabled) info.textContent = "Case is not busy (no active step) — editing/adding process data is disabled.";
    else info.textContent = "";
  }
}

async function refreshUserCurrent() {
  const c = state.userPortal.currentCase;
  if (!c) {
    state.userPortal.currentStep = null;
    renderUserCurrent();
    updateProcessDataFormEnabled();
    return;
  }
  try {
    const step = await api.get(`/cases/${c.caseno}/current-step`);
    state.userPortal.currentStep = step;
  } catch (e) {
    // If 404, there may be no active step (process completed)
    state.userPortal.currentStep = null;
  }
  renderUserCurrent();
  updateProcessDataFormEnabled();
}

function bindUserPortal() {
  const searchForm = document.getElementById("user-search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = document.getElementById("user-search-query")?.value.trim();
      if (!q) return;
      const resultsEl = document.getElementById("user-search-results");
      if (resultsEl) resultsEl.innerHTML = "<div class='item'>Searching...</div>";
      try {
        const roles = Array.isArray(state.user?.roles) ? state.user.roles : [state.user?.role].filter(Boolean);
        const isAdmin = roles.includes("admin");
        const num = Number(q);
        const isNumeric = !Number.isNaN(num) && /^\d+$/.test(q);

        if (isNumeric) {
          // Try by case number first
          let item = null;
          try {
            item = await api.get(`/cases/${num}`);
          } catch { /* ignore 404 or errors for fallback */ }
          let results = [];
          if (item && (isAdmin || item.usrid === state.user.username)) {
            results = [item];
          }
          // Fallback: search by client_id among user's cases if not found/authorized
          if (results.length === 0) {
            const items = await listMyCases();
            const normQ = q.toLowerCase();
            results = items.filter(c => (c.client_id || "").toLowerCase().includes(normQ));
          }
          renderSearchResults(results);
        } else {
          // Search by client id among user's cases (partial, case-insensitive)
          const items = await listMyCases();
          const normQ = q.toLowerCase();
          const filtered = items.filter(c => (c.client_id || "").toLowerCase().includes(normQ));
          renderSearchResults(filtered);
        }
      } catch (err) {
        notify(`Search failed: ${err.message}`, "error");
        renderSearchResults([]);
      }
    });
  }

  const createForm = document.getElementById("user-create-case-form");
  if (createForm) {
    createForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!state.user) {
        notify("Please login first", "error");
        return;
      }
      const ptype = document.getElementById("user-process-type-no")?.value;
      const clientId = document.getElementById("user-client-id")?.value.trim();
      const clientType = document.getElementById("user-client-type")?.value.trim();
      if (!ptype || !clientId || !clientType) {
        notify("Please complete all fields", "error");
        return;
      }
      try {
        const body = { client_id: clientId, client_type: clientType, usrid: state.user.username };
        const created = await api.post(`/create-case/?process_type_no=${parseInt(ptype, 10)}`, body);
        state.userPortal.currentCase = created;
        notify(`Case #${created.caseno} created`, "success");
        await refreshUserCurrent();
        await loadCaseProcessData(created.caseno);
        await loadCaseSteps(created.caseno);
      } catch (err) {
        notify(`Create case failed: ${err.message}`, "error");
      }
    });
  }

  const pdForm = document.getElementById("user-procdata-form");
  if (pdForm) {
    pdForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const c = state.userPortal.currentCase;
      if (!c) {
        notify("Create or select a case first", "error");
        return;
      }
      // Ensure we have the latest current step
      if (!state.userPortal.currentStep) {
        await refreshUserCurrent();
      }
      const step = state.userPortal.currentStep;
      if (!step) {
        notify("No active step to attach data to (process may be complete)", "error");
        return;
      }
      const pdType = document.getElementById("user-pd-type")?.value;
      const field = document.getElementById("user-pd-field")?.value.trim();
      const value = document.getElementById("user-pd-value")?.value;
      if (!pdType || !field) {
        notify("Please provide process data type and field", "error");
        return;
      }
      try {
        await api.post(`/processes/${step.processno}/data/`, {
          process_data_type_no: parseInt(pdType, 10),
          fieldname: field,
          value
        });
        notify("Process data added", "success");
        document.getElementById("user-pd-field").value = "";
        document.getElementById("user-pd-value").value = "";
        await loadCaseProcessData(c.caseno);
      } catch (err) {
        notify(`Add process data failed: ${err.message}`, "error");
      }
    });
  }

  const pdEditForm = document.getElementById("user-procdata-edit-form");
  if (pdEditForm) {
    pdEditForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const c = state.userPortal.currentCase;
      if (!c) {
        notify("Select a case first", "error");
        return;
      }
      if (!state.userPortal.currentStep) {
        await refreshUserCurrent();
      }
      if (!state.userPortal.currentStep) {
        notify("Case is not busy — cannot update data", "error");
        return;
      }
      const id = document.getElementById("user-pd-edit-id")?.value;
      const pdType = document.getElementById("user-pd-edit-type")?.value;
      const field = document.getElementById("user-pd-edit-field")?.value.trim();
      const value = document.getElementById("user-pd-edit-value")?.value;
      if (!id) {
        notify("No process data selected for edit", "error");
        return;
      }
      if (!pdType || !field) {
        notify("Please provide process data type and field", "error");
        return;
      }
      try {
        await api.put(`/process-data/${parseInt(id, 10)}`, {
          process_data_type_no: parseInt(pdType, 10),
          fieldname: field,
          value
        });
        notify("Process data updated", "success");
        // Clear edit form
        const idEl = document.getElementById("user-pd-edit-id"); if (idEl) idEl.value = "";
        const fieldEl = document.getElementById("user-pd-edit-field"); if (fieldEl) fieldEl.value = "";
        const valueEl = document.getElementById("user-pd-edit-value"); if (valueEl) valueEl.value = "";
        await loadCaseProcessData(c.caseno);
      } catch (err) {
        notify(`Update process data failed: ${err.message}`, "error");
      }
    });
  }

  const doneBtn = document.getElementById("user-done-btn");
  if (doneBtn) {
    doneBtn.addEventListener("click", async () => {
      const step = state.userPortal.currentStep;
      const c = state.userPortal.currentCase;
      if (!c) {
        notify("Create or select a case first", "error");
        return;
      }
      if (!step) {
        notify("No active step to close", "error");
        return;
      }
      try {
        await api.post(`/steps/${step.stepno}/close`, { rule_data: {} });
        notify("Step closed", "success");
        await refreshUserCurrent();
        if (c?.caseno) {
          await loadCaseProcessData(c.caseno);
          await loadCaseSteps(c.caseno);
        }
      } catch (err) {
        notify(`Close step failed: ${err.message}`, "error");
      }
    });
  }
}

async function loadUserPortal() {
  if (!state.token) return;
  await Promise.all([
    loadUserProcessTypes(),
    loadUserProcessDataTypes(),
  ]);
}

// Clears common inputs and transient lists/details without a full reload
function clearFieldsAndLists() {
  // Auth forms
  const idsToClear = [
    "username","password","reg-username","reg-password",
    // User portal create/search
    "user-search-query","user-client-id","user-client-type","user-pd-field","user-pd-value"
  ];
  idsToClear.forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });

  // Selects to reset
  const selectsToReset = ["user-process-type-no","user-pd-type"];
  selectsToReset.forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });

  // Checkboxes
  const checksToUncheck = ["pd-is-active","pd-upd-is-active"];
  checksToUncheck.forEach(id => { const el = document.getElementById(id); if (el) el.checked = false; });

  // Detail/list containers to clear (transient views)
  const containersToClear = [
    "status-detail","process-type-detail","process-data-type-detail","process-definition-detail","task-detail",
    "user-current","user-procdata-list","user-steps-list","user-search-results"
  ];
  containersToClear.forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ""; });

  // Reset user portal state and disable add-data when no busy step
  state.userPortal.currentCase = null;
  state.userPortal.currentStep = null;
  updateProcessDataFormEnabled?.();
}

window.addEventListener("DOMContentLoaded", () => {
  bindAuth();
  bindTabs();
  bindForms();
  bindUserPortal();
  setAuthStatus();
  loadUserPortal().catch(() => {});
});
