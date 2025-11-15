/* ====== Sauvegarde locale (localStorage) ====== */
const STORAGE_KEY = "dtn_smartops_board_v1";

function id() {
  return Math.random().toString(36).slice(2, 9);
}

function getDefaultState() {
  return {
    columns: [
      { id: id(), title: "devis à faire", cards: [] },
      { id: id(), title: "devis validé", cards: [] },
      { id: id(), title: "rdv programmé", cards: [] },
      { id: id(), title: "facture à envoyer", cards: [] },
    ],
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return getDefaultState();
    const parsed = JSON.parse(raw);
    if (!parsed.columns) throw new Error("state invalide");
    return parsed;
  } catch (e) {
    console.warn("Impossible de charger l'état, utilisation du défaut :", e);
    return getDefaultState();
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn("Impossible de sauvegarder l'état :", e);
  }
}

/* ====== État ====== */
let state = loadState();

const board = document.getElementById("board");
const newColumnName = document.getElementById("newColumnName");
const addColumnBtn = document.getElementById("addColumnBtn");
const openDrawerBtn = document.getElementById("openDrawerBtn");

/* ====== Drawer ====== */
const drawer = document.getElementById("drawer");
const drawerBackdrop = document.getElementById("drawerBackdrop");
const drawerClose = document.getElementById("drawerClose");
const taskForm = document.getElementById("taskForm");
const categorySelect = document.getElementById("category");
const customCatWrap = document.getElementById("customCatWrap");
const cancelTask = document.getElementById("cancelTask");

/* ====== Modal ====== */
const modal = document.getElementById("cardModal");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalClose = document.getElementById("modalClose");
const modalTitle = document.getElementById("modalTitle");
const modalBody = document.getElementById("modalBody");
const modalEdit = document.getElementById("modalEdit");
const modalDelete = document.getElementById("modalDelete");

let modalContext = { columnId: null, cardId: null };

/* ====== Rendu ====== */
function render() {
  board.innerHTML = "";
  state.columns.forEach(col => {
    const colEl = document.createElement("section");
    colEl.className = "column";
    colEl.dataset.columnId = col.id;
    colEl.innerHTML = `
      <header class="column-head">
        <h2 contenteditable="true" class="column-title">${col.title}</h2>
        <div class="menu">
          <button class="icon-btn" data-menu="open">⋯</button>
          <div class="menu-list">
            <button data-action="rename">Renommer</button>
            <button data-action="delete">Supprimer</button>
          </div>
        </div>
      </header>
      <div class="cards" data-dropzone></div>
      <div class="column-foot">
        <button class="btn btn-accent" data-action="addCard">+ Nouvelle tâche</button>
      </div>
    `;
    const list = colEl.querySelector(".cards");

    col.cards.forEach(card => {
      const c = document.createElement("article");
      c.className = "card";
      c.draggable = true;
      c.dataset.cardId = card.id;
      c.innerHTML = `
        <div class="card-name">${card.firstname} <b>${card.lastname.toUpperCase()}</b></div>
        <div class="card-meta">
          <span class="chip">${card.category}</span>
          ${card.date ? `<span class="chip">${fmtDate(card.date)}</span>` : ""}
        </div>
        <button class="icon-btn card-menu" title="Options">⋯</button>
        <div class="menu-list">
          <button data-action="open">Ouvrir</button>
          <button data-action="edit">Modifier</button>
          <button data-action="delete">Supprimer</button>
        </div>
      `;

      // Click sur le nom = ouvrir fiche
      c.querySelector(".card-name").addEventListener("click", () => openCard(col.id, card.id));

      // Drag & drop
      c.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", JSON.stringify({ fromCol: col.id, cardId: card.id }));
      });

      list.appendChild(c);
    });

    // Dropzone
    list.addEventListener("dragover", (e) => e.preventDefault());
    list.addEventListener("drop", (e) => {
      e.preventDefault();
      const data = JSON.parse(e.dataTransfer.getData("text/plain"));
      moveCard(data.fromCol, col.id, data.cardId);
    });

    board.appendChild(colEl);
  });

  wireEvents();
  // 🔐 Sauvegarde à chaque rendu
  saveState();
}

function wireEvents() {
  // menu colonnes
  document.querySelectorAll('[data-menu="open"]').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      closeMenus();
      btn.nextElementSibling.classList.add("open");
    };
  });

  document.querySelectorAll(".menu-list [data-action]").forEach(btn => {
    btn.onclick = () => {
      const section = btn.closest("section");
      const colId = section.dataset.columnId;
      const action = btn.dataset.action;

      if (action === "delete") {
        state.columns = state.columns.filter(c => c.id !== colId);
        render();
      }
      if (action === "rename") {
        const title = section.querySelector(".column-title");
        title.focus();
        document.execCommand("selectAll", false, null);
        // On sauve le nouveau titre quand on sort du champ
        title.onblur = () => {
          const col = state.columns.find(c => c.id === colId);
          col.title = title.textContent.trim() || col.title;
          render();
        };
      }
      closeMenus();
    };
  });

  // bouton nouvelle tâche dans une colonne
  document.querySelectorAll('[data-action="addCard"]').forEach(btn => {
    btn.onclick = () => openDrawer(btn.closest("section").dataset.columnId);
  });

  // menu d’une carte
  document.querySelectorAll(".card .card-menu").forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      closeMenus();
      btn.nextElementSibling.classList.add("open");
    };
  });

  document.querySelectorAll(".card .menu-list [data-action]").forEach(btn => {
    btn.onclick = () => {
      const cardEl = btn.closest(".card");
      const colId = btn.closest("section").dataset.columnId;
      const cardId = cardEl.dataset.cardId;
      const action = btn.dataset.action;

      if (action === "open") openCard(colId, cardId);
      if (action === "edit") openDrawer(colId, cardId);
      if (action === "delete") {
        const col = state.columns.find(c => c.id === colId);
        col.cards = col.cards.filter(c => c.id !== cardId);
        render();
      }
      closeMenus();
    };
  });

  // fermer menus au clic dehors
  document.body.onclick = closeMenus;
}

function closeMenus() {
  document.querySelectorAll(".menu-list.open").forEach(m => m.classList.remove("open"));
}

/* ====== Drawer logique ====== */
let currentColumnForNew = null;
let editingCardId = null;

openDrawerBtn.onclick = () => openDrawer();
drawerClose.onclick = closeDrawer;
drawerBackdrop.onclick = closeDrawer;
cancelTask.onclick = closeDrawer;

categorySelect.onchange = () => {
  if (categorySelect.value === "Autre") {
    customCatWrap.classList.remove("hidden");
  } else {
    customCatWrap.classList.add("hidden");
  }
};

function openDrawer(columnId = null, cardId = null) {
  currentColumnForNew = columnId;
  editingCardId = cardId;

  // Reset formulaire
  taskForm.reset();
  customCatWrap.classList.add("hidden");

  if (cardId) {
    // Édition : remplir les champs
    const { card } = findCard(columnId, cardId);
    taskForm.firstname.value = card.firstname;
    taskForm.lastname.value = card.lastname;
    taskForm.phone.value = card.phone || "";
    taskForm.email.value = card.email || "";
    taskForm.address.value = card.address || "";
    taskForm.date.value = card.date || "";
    taskForm.notes.value = card.notes || "";
    // catégorie
    if (["Électricité","Télécom","GC","Viabilisation","Panneaux solaires","Borne IRVE"].includes(card.category)) {
      categorySelect.value = card.category;
    } else {
      categorySelect.value = "Autre";
      customCatWrap.classList.remove("hidden");
      taskForm.customCategory.value = card.category;
    }
  }

  drawer.classList.add("open");
  drawerBackdrop.classList.add("show");
}

function closeDrawer() {
  drawer.classList.remove("open");
  drawerBackdrop.classList.remove("show");
  editingCardId = null;
}

taskForm.onsubmit = (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(taskForm).entries());
  let category = data.category === "Autre" && data.customCategory ? data.customCategory : data.category;

  if (editingCardId) {
    // update
    const { card } = findCard(currentColumnForNew, editingCardId);
    Object.assign(card, {
      firstname: data.firstname.trim(),
      lastname: data.lastname.trim(),
      phone: data.phone.trim(),
      email: data.email.trim(),
      address: data.address.trim(),
      category,
      date: data.date,
      notes: data.notes.trim(),
    });
  } else {
    // add dans la première colonne si aucune sélection
    const col = state.columns.find(c => c.id === (currentColumnForNew || state.columns[0].id));
    col.cards.push({
      id: id(),
      firstname: data.firstname.trim(),
      lastname: data.lastname.trim(),
      phone: data.phone.trim(),
      email: data.email.trim(),
      address: data.address.trim(),
      category,
      date: data.date,
      notes: data.notes.trim(),
    });
  }

  render();
  closeDrawer();
};

/* ====== Déplacement de carte ====== */
function moveCard(fromColId, toColId, cardId) {
  if (fromColId === toColId) return;
  const from = state.columns.find(c => c.id === fromColId);
  const to = state.columns.find(c => c.id === toColId);
  const idx = from.cards.findIndex(c => c.id === cardId);
  const [card] = from.cards.splice(idx, 1);
  to.cards.push(card);
  render();
}

function findCard(colId, cardId) {
  const col = state.columns.find(c => c.id === colId);
  const card = col.cards.find(c => c.id === cardId);
  return { col, card };
}

/* ====== Fiche client (modale) ====== */
function openCard(colId, cardId) {
  const { card } = findCard(colId, cardId);
  modalContext = { columnId: colId, cardId };

  modalTitle.textContent = `${card.firstname} ${card.lastname.toUpperCase()}`;
  modalBody.innerHTML = `
    <div class="kv"><span>Catégorie</span><b>${escapeHtml(card.category || "-")}</b></div>
    <div class="kv"><span>Téléphone</span><b>${escapeHtml(card.phone || "-")}</b></div>
    <div class="kv"><span>Email</span><b>${escapeHtml(card.email || "-")}</b></div>
    <div class="kv"><span>Adresse</span><b>${escapeHtml(card.address || "-")}</b></div>
    <div class="kv"><span>Date RDV</span><b>${card.date ? fmtDate(card.date) : "-"}</b></div>
    <div class="kv"><span>Notes</span><b>${escapeHtml(card.notes || "-")}</b></div>
  `;

  modal.classList.add("open");
  modalBackdrop.classList.add("show");
}

modalClose.onclick = closeModal;
modalBackdrop.onclick = closeModal;

modalEdit.onclick = () => {
  closeModal();
  openDrawer(modalContext.columnId, modalContext.cardId);
};

modalDelete.onclick = () => {
  const col = state.columns.find(c => c.id === modalContext.columnId);
  col.cards = col.cards.filter(c => c.id !== modalContext.cardId);
  closeModal();
  render();
};

function closeModal() {
  modal.classList.remove("open");
  modalBackdrop.classList.remove("show");
}

/* ====== Colonnes ====== */
addColumnBtn.onclick = () => {
  const name = (newColumnName.value || "").trim();
  if (!name) return;
  state.columns.push({ id: id(), title: name, cards: [] });
  newColumnName.value = "";
  render();
};

/* ====== Util ====== */
function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function fmtDate(d) {
  try { return new Date(d).toLocaleDateString("fr-FR"); } catch { return d; }
}

/* Init */
render();
